from flet import (
    BottomAppBar,
    Colors,
    Column,
    Container,
    ControlEvent,
    FontWeight,
    Icons,
    IconButton,
    Image,
    MainAxisAlignment,
    padding,
    Page,
    Row,
    Slider,
    Text,
    TextOverflow,
)
from flet_audio import (
    Audio,
    AudioState,
    AudioStateChangeEvent
)
from random import choice
from json import dumps, loads

from shared import (
    format_time,
    get_album_cover,
    load_music_metadata
)
from models import MusicsModel, PlayerModel


def player(page: Page):
    ZERO_TIME = '--:--'

    player_model = PlayerModel()
    musics_model = MusicsModel()

    musics_list = None
    musics_queue = {'prev_music': None, 'next_music': None}
    volume_cache = 0.5
    played_music_cache = []
    current_music_cache = None
    position_update_counter = 0

    is_playing = False
    is_muted = False
    is_shuffle = False
    is_repeat = False

    def on_play_music_subscribe(_, args: dict):
        nonlocal musics_list

        music_to_play = args.get('music_to_play')
        musics_list = args.get('musics_list')

        update_music_play(music_to_play)
        player_model.update_info({
            'musics_list': dumps(musics_list),
            'current_album': music_to_play.get('album')
        })

    def on_pause_music_subscribe(_, args: dict):
        on_pause_music(None)

    def on_resume_music_subscribe(_, args: dict):
        on_play_music(None)

    def on_folder_removed_subscribe(_, args: dict):
        nonlocal musics_list, played_music_cache, current_music_cache

        updated_musics_list = musics_model.all_musics

        if not updated_musics_list:
            updated_musics_list = []

        if played_music_cache:
            played_music_cache = [music for music in played_music_cache
                                if any(m.get('filename') == music.get('filename')
                                      for m in updated_musics_list)]

        musics_list = updated_musics_list

        if current_music_cache:
            music_exists = any(m.get('filename') == current_music_cache.get('filename')
                              for m in musics_list)

            if not music_exists:
                update_play_button(is_play=False)
                update_current_time(0)
                audio.pause()

                if musics_list:
                    update_music_play(musics_list[0])
                else:
                    current_music_cache = None
                    music_title.value = 'Titulo da musica'
                    music_artist.value = 'Nome do artista'
                    music_cover.src_base64 = None
                    music_cover.src = 'app/assets/album_placeholder.png'
                    end_time.value = ZERO_TIME
                    current_time.value = ZERO_TIME
                    progress_time.value = 0

                    page.update()

                    player_model.update_info({
                        'audio_duration': None,
                        'audio_current_position': None,
                        'current_music': None,
                        'current_album': None,
                        'prev_music': None,
                        'next_music': None
                    })

        player_model.update_info({
            'musics_list': dumps(musics_list),
            'played_music': dumps(played_music_cache),
        })

    def on_play_music(_):
        if current_music_cache:
            audio.resume()

            update_play_button(is_play=True)

            page.update()
            player_model.update_info({ 'is_pause': 'False' })

    def on_pause_music(_):
        audio.pause()

        update_play_button(is_play=False)

        page.update()

    def on_prev_music(_):
        if is_shuffle:
            if played_music_cache:
                current_index = played_music_cache.index(current_music_cache)
                prev_music = played_music_cache[current_index - 1] if current_index > 0 else None
            else:
                prev_music = None
        else:
            prev_music = musics_queue.get('prev_music')

        if prev_music:
            update_music_play(prev_music)
        else:
            audio.seek(0)
            audio.resume()


    def on_next_music(_):
        if is_shuffle:
            if current_music_cache in played_music_cache:
                current_index = played_music_cache.index(current_music_cache)

                available_musics = [
                    music for music in musics_list
                    if music not in played_music_cache
                ]

                if current_index < len(played_music_cache) - 1:
                    next_music = played_music_cache[current_index + 1]
                elif available_musics:
                    next_music = choice(available_musics)
                elif is_repeat == 'all':
                    played_music_cache.clear()
                    next_music = choice(musics_list)
                else:
                    next_music = None
            else:
                next_music = choice(musics_list)
        else:
            next_music = musics_queue.get('next_music')

        if next_music:
            update_music_play(next_music)

    def on_shuffle_music(_):
        nonlocal is_shuffle

        is_shuffle = not is_shuffle

        if is_shuffle:
            button_shuffle.tooltip = 'Embaralhar: Ativado'
            button_shuffle.icon_color = Colors.RED_ACCENT_200
        else:
            button_shuffle.tooltip = 'Embaralhar: Desativado'
            button_shuffle.icon_color = Colors.GREY_600

        played_music_cache.clear()
        button_shuffle.update()
        player_model.update_info({'is_shuffle': f'{is_shuffle}'})

    def on_repeat_music(_):
        nonlocal is_repeat

        if not is_repeat:
            is_repeat = 'all'
            button_repeat.tooltip = 'Repetir: Tudo'
        elif is_repeat == 'all':
            is_repeat = 'one'
            button_repeat.icon = Icons.REPEAT_ONE
            button_repeat.tooltip = 'Repetir: Um'
        elif is_repeat == 'one':
            is_repeat = False
            button_repeat.tooltip = 'Repetir: Desativado'
            button_repeat.icon = Icons.REPEAT

        if not is_repeat:
            button_repeat.icon_color = Colors.GREY_600
        else:
            button_repeat.icon_color = Colors.RED_ACCENT_200

        button_repeat.update()
        player_model.update_info({'is_repeat': f'{is_repeat}'})

    def on_audio_loader(_):
        # Only play if explicitly requested, not during initial loading
        if not getattr(audio, '_initial_load', False):
            audio.play()
        else:
            # For initial load, just update the duration info without playing
            audio.seek(audio._current_position)
            audio._initial_load = False

        duration = audio.get_duration()
        if duration is not None:
            player_model.update_info({ 'audio_duration': duration })

    def on_audio_state_changed(event: AudioStateChangeEvent):
        audio_duration = audio.get_duration()

        if event.state == AudioState.COMPLETED:
            next_music = musics_queue.get('next_music')

            if is_repeat == 'one':
                next_music = current_music_cache
            elif is_shuffle:
                available_musics = [
                    music for music in musics_list
                    if music not in played_music_cache
                ]

                if current_music_cache in played_music_cache:
                    current_index = played_music_cache.index(current_music_cache)

                    if current_index < len(played_music_cache) - 1:
                        next_music = played_music_cache[current_index + 1]
                    elif available_musics:
                        next_music = choice(available_musics)
                    elif is_repeat == 'all':
                        played_music_cache.clear()
                        next_music = choice(musics_list)
                    else:
                        next_music = None
                else:
                    next_music = choice(available_musics)
            elif is_repeat == 'all' and not next_music:
                next_music = musics_list[0]

            if next_music:
                update_music_play(next_music)
            else:
                update_play_button(is_play=False)
                update_current_time(0)
                update_end_time(0, audio_duration)
                update_progress_time(0, audio_duration)
                player_model.update_info({ 'is_playing': 'False' })

        elif event.state == AudioState.PAUSED:
            player_model.update_info({
                'is_pause': 'True',
                'is_playing': 'False'
            })
        elif event.state == AudioState.PLAYING:
            player_model.update_info({
                'is_pause': 'False',
                'is_playing': 'True'
            })


        page.pubsub.send_all_on_topic(
            'play_music_state',
            {
                'state': event.state,
                'music_key': current_music_cache.get('filename') if current_music_cache else None,
                'album_key': current_music_cache.get('album') if current_music_cache else None,
            }
        )

    def on_audio_position_changed(_):
        nonlocal position_update_counter
        audio_current_position = audio.get_current_position()
        audio_duration = None

        try:
            audio_duration = audio.get_duration()
        except Exception as err:
            print(f'Error getting duration in position change: {err}')

        if audio_current_position and audio_current_position > 0:
            update_current_time(audio_current_position)
            update_end_time(audio_current_position, audio_duration)
            update_progress_time(audio_current_position, audio_duration)

            # Update position in database periodically based on event count
            position_update_counter += 1
            if position_update_counter >= 3:
                player_model.update_info({'audio_current_position': audio_current_position})
                position_update_counter = 0

    def on_progress_time_seek(event: ControlEvent):
        audio.seek(int(float(event.data)))

        if is_playing:
            audio.resume()

    def on_progress_time_change(_):
        audio.pause()

    def on_volume_change(event: ControlEvent):
        volume = round(event.control.value, 2)

        update_volume_icon(volume)

        audio.volume = volume

        audio.update()

    def on_volume_change_end(event: ControlEvent):
        volume = round(event.control.value, 2)

        player_model.update_info({ 'volume': volume })

    def on_volume_mute(_):
        nonlocal is_muted, volume_cache

        is_muted = not is_muted

        if is_muted:
            volume_cache = audio.volume
            audio.volume = 0
            update_volume_icon(0)
        else:
            audio.volume = volume_cache
            update_volume_icon(volume_cache)

        audio.update()
        player_model.update_info({'is_muted': f'{is_muted}'})

    def update_music_play(music_to_play: dict):
        nonlocal current_music_cache

        current_music_cache = music_to_play

        audio.src = music_to_play.get('filename')
        audio.play()

        update_music_info(music_to_play)
        update_play_button(is_play=True)
        update_musics_queue(music_to_play)

        if music_to_play not in played_music_cache:
            played_music_cache.append(music_to_play)

        page.update()

        player_model.update_info({
            'current_music': dumps(music_to_play),
            'current_album': music_to_play.get('album'),
            'played_music': dumps(played_music_cache),
        })

    def update_musics_queue(music_to_play: dict):
        nonlocal musics_queue

        if music_to_play in musics_list:
            index = musics_list.index(music_to_play)

            if index == 0:
                prev_music = None
                next_music = musics_list[1] if len(musics_list) > 1 else None
            elif index == len(musics_list) - 1:
                prev_music = musics_list[index - 1]
                next_music = None
            else:
                prev_music = musics_list[index - 1]
                next_music = musics_list[index + 1]

            musics_queue = { 'prev_music': prev_music, 'next_music': next_music }
            player_model.update_info(
                { 'prev_music': dumps(prev_music), 'next_music': dumps(next_music) }
            )

    def update_current_time(audio_current_position: int):
        current_time.value = format_time(audio_current_position)
        page.update()

    def update_end_time(audio_current_position: int, audio_duration: int):
        try:
            if audio_duration is None:
                end_time.value = ZERO_TIME
            else:
                new_time = audio_duration - audio_current_position
                end_time.value = format_time(new_time)
            page.update()
        except Exception as err:
            print(f'Error updating end time: {err}')
            end_time.value = ZERO_TIME
            page.update()

    def update_progress_time(current_position: int, end_position: int):
        try:
            progress_time.value = current_position
            if end_position is not None and end_position > 0:
                progress_time.max = end_position

            page.update()
        except Exception as err:
            print(f'Error updating progress time: {err}')

    def update_music_info(music: dict):
        music_title.value = music.get('title')
        music_artist.value = music.get('artist')
        end_time.value = music.get('duration')
        current_time.value = '00:00'
        progress_time.value = 0

        update_music_cover(music.get('filename'))

        page.update()

    def update_music_cover(filename: str):
        music = load_music_metadata(file=filename, with_image=True)
        cover = get_album_cover(music)

        music_cover.src_base64 = cover

        page.update()

    def update_play_button(is_play: bool):
        nonlocal is_playing

        is_playing = is_play

        if is_play:
            button_play.visible = False
            button_pause.visible = True
            player_model.update_info({ 'is_playing': 'True' })
        else:
            button_play.visible = True
            button_pause.visible = False
            player_model.update_info({ 'is_playing': 'False' })

        page.update()

    def update_volume_icon(volume: float):
        if volume >= 0.02 and volume <= 0.44:
            button_volume.icon = Icons.VOLUME_DOWN
        elif volume >= 0.45:
            button_volume.icon = Icons.VOLUME_UP
        else:
            button_volume.icon = Icons.VOLUME_OFF
        page.update()

    def load_player_settings():
        nonlocal musics_list, played_music_cache, current_music_cache, is_shuffle, is_repeat, is_muted, volume_cache, musics_queue

        player_info = player_model.all_info

        if player_info:
            if 'volume' in player_info and player_info['volume'] is not None:
                volume = float(player_info['volume'])
                audio.volume = volume
                volume_cache = volume
                volume_slider.value = volume
                update_volume_icon(volume)

            if 'is_muted' in player_info and player_info['is_muted'] is not None:
                is_muted = player_info['is_muted'].lower() == 'true'
                if is_muted:
                    audio.volume = 0
                    update_volume_icon(0)

            if 'is_shuffle' in player_info and player_info['is_shuffle'] is not None:
                is_shuffle = player_info['is_shuffle'].lower() == 'true'
                if is_shuffle:
                    button_shuffle.tooltip = 'Embaralhar: Ativado'
                    button_shuffle.icon_color = Colors.RED_ACCENT_200

            if 'is_repeat' in player_info and player_info['is_repeat'] not in [None, 'False']:
                is_repeat = player_info['is_repeat']
                if is_repeat == 'all':
                    button_repeat.tooltip = 'Repetir: Tudo'
                    button_repeat.icon_color = Colors.RED_ACCENT_200
                elif is_repeat == 'one':
                    button_repeat.tooltip = 'Repetir: Um'
                    button_repeat.icon = Icons.REPEAT_ONE
                    button_repeat.icon_color = Colors.RED_ACCENT_200

            if 'musics_list' in player_info and player_info['musics_list']:
                try:
                    musics_list = loads(player_info['musics_list'])
                except Exception as err:
                    print(f'Error loading musics list: {err}')
                    musics_list = []

            if 'played_music' in player_info and player_info['played_music']:
                try:
                    played_music_cache = loads(player_info['played_music'])
                except Exception as err:
                    print(f'Error loading played music: {err}')
                    played_music_cache = []

            if 'current_music' in player_info and player_info['current_music']:
                try:
                    current_music = loads(player_info['current_music'])
                    current_music_cache = current_music
                    update_music_info(current_music)
                    update_musics_queue(current_music)

                    # Set the source but don't play automatically
                    audio._initial_load = True
                    audio.src = current_music.get('filename')

                    update_play_button(is_play=False)
                except Exception as err:
                    print(f'Error loading current music: {err}')

            if 'audio_current_position' in player_info and player_info['audio_current_position'] is not None:
                try:
                    position = int(player_info['audio_current_position'])
                    audio._current_position = position

                    if 'audio_duration' in player_info and player_info['audio_duration'] is not None:
                        duration = int(player_info['audio_duration'])
                        update_current_time(position)
                        update_end_time(position, duration)
                        update_progress_time(position, duration)
                except Exception as err:
                    print(f'Error setting audio position: {err}')

        page.update()

    audio = Audio(
        src='none',
        volume=0.5,
        balance=0,
        on_loaded=on_audio_loader,
        on_state_changed=on_audio_state_changed,
        on_position_changed=on_audio_position_changed,
    )
    audio._initial_load = False  # Custom attribute to track initial loading

    current_time = Text(
        value=ZERO_TIME,
        color=Colors.WHITE,
    )

    progress_time = Slider(
        min=0,
        active_color=Colors.RED_ACCENT_200,
        inactive_color=Colors.GREY_800,
        on_change_end=on_progress_time_seek,
        on_change_start=on_progress_time_change,
    )

    end_time = Text(
        value=ZERO_TIME,
        color=Colors.WHITE,
    )

    music_cover = Image(
        width=62,
        height=62,
        border_radius=4,
        src='app/assets/album_placeholder.png',
    )

    music_title = Text(
        value='Titulo da musica',
        color=Colors.WHITE,
        size=16,
        weight=FontWeight.W_500,
        max_lines=1,
        overflow=TextOverflow.ELLIPSIS,
    )

    music_artist = Text(
        value='Nome do artista',
        color=Colors.GREY_400,
        size=14,
        max_lines=1,
    )

    button_play = IconButton(
        tooltip='Executar',
        icon=Icons.PLAY_ARROW,
        icon_color=Colors.GREY_900,
        icon_size=30,
        bgcolor=Colors.WHITE,
        hover_color=Colors.TRANSPARENT,
        visible=True,
        on_click=on_play_music
    )

    button_pause = IconButton(
        tooltip='Pausar',
        icon=Icons.PAUSE,
        icon_color=Colors.GREY_900,
        icon_size=30,
        bgcolor=Colors.WHITE,
        hover_color=Colors.TRANSPARENT,
        visible=False,
        on_click=on_pause_music
    )

    button_shuffle = IconButton(
        icon=Icons.SHUFFLE,
        icon_color=Colors.GREY_600,
        hover_color=Colors.TRANSPARENT,
        tooltip='Embaralhar: Desativado',
        highlight_color=Colors.with_opacity(
            0.1,
            Colors.GREY_600
        ),
        on_click=on_shuffle_music
    )

    button_repeat = IconButton(
        icon=Icons.REPEAT,
        icon_color=Colors.GREY_600,
        hover_color=Colors.TRANSPARENT,
        tooltip='Repetir: Desativado',
        highlight_color=Colors.with_opacity(
            0.1,
            Colors.GREY_600
        ),
        on_click=on_repeat_music
    )

    button_volume = IconButton(
        tooltip='Volume',
        icon=Icons.VOLUME_UP,
        icon_color=Colors.WHITE,
        hover_color=Colors.TRANSPARENT,
        highlight_color=Colors.with_opacity(
            0.1,
            Colors.GREY_600
        ),
        on_click=on_volume_mute
    )

    volume_slider = Slider(
        min=0,
        max=1,
        value=0.5,
        width=120,
        label='{value}',
        active_color=Colors.RED_ACCENT_200,
        inactive_color=Colors.GREY_800,
        on_change=on_volume_change,
        on_change_end=on_volume_change_end,
    )

    player = BottomAppBar(
        height=120,
        bgcolor='#1D1D1D',
        padding=padding.symmetric(vertical=10, horizontal=15),
        content=Column(
            spacing=15,
            controls=[
                Row(
                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        current_time,
                        Container(
                            expand=True,
                            height=10,
                            content=progress_time
                        ),
                        end_time,
                    ]
                ),
                Row(
                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        Row(
                            controls=[
                                music_cover,
                                Column(
                                    width=180,
                                    spacing=5,
                                    controls=[
                                        music_title,
                                        music_artist
                                    ]
                                )
                            ]
                        ),
                        Row(
                            controls=[
                                button_shuffle,
                                IconButton(
                                    tooltip='Voltar',
                                    icon=Icons.SKIP_PREVIOUS,
                                    icon_color=Colors.WHITE,
                                    icon_size=28,
                                    hover_color=Colors.TRANSPARENT,
                                    highlight_color=Colors.with_opacity(
                                        0.1,
                                        Colors.GREY_600
                                    ),
                                    on_click=on_prev_music
                                ),
                                button_play,
                                button_pause,
                                IconButton(
                                    icon_size=28,
                                    tooltip='Avançar',
                                    icon=Icons.SKIP_NEXT,
                                    icon_color=Colors.WHITE,
                                    hover_color=Colors.TRANSPARENT,
                                    highlight_color=Colors.with_opacity(
                                        0.1,
                                        Colors.GREY_600
                                    ),
                                    on_click=on_next_music
                                ),
                                button_repeat
                            ]
                        ),
                        Row(
                            spacing=-5,
                            controls=[
                                button_volume,
                                volume_slider
                            ],
                        )
                    ]
                )
            ]
        )
    )

    page.overlay.append(audio)

    page.pubsub.subscribe_topic('play_music', on_play_music_subscribe)
    page.pubsub.subscribe_topic('pause_music', on_pause_music_subscribe)
    page.pubsub.subscribe_topic('resume_music', on_resume_music_subscribe)
    page.pubsub.subscribe_topic('folder_removed', on_folder_removed_subscribe)

    load_player_settings()

    return player
