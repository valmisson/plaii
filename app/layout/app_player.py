from flet import *
from flet_audio import (
    Audio,
    AudioState,
    AudioStateChangeEvent
)

from shared import (
    format_time,
    get_album_cover,
    load_music_metadata
)

def player(page: Page):
    ZERO_TIME = '--:--'

    musics_list = None
    musics_queue = None
    volume_cache = 0.5
    is_muted = False
    is_shuffle = False

    def on_play_music_subscribe(_, args: dict):
        nonlocal musics_list

        music_to_play = args.get('music_to_play')
        musics_list = args.get('musics_list')

        update_music_play(music_to_play)

    def on_play_music(_):
        audio.resume()

        update_play_button(is_play=True)

        page.update()

    def on_pause_music(_):
        audio.pause()

        update_play_button(is_play=False)

        page.update()

    def on_prev_music(_):
        music_to_play = musics_queue.get('prev_music')

        update_music_play(music_to_play)

    def on_next_music(_):
        music_to_play = musics_queue.get('next_music')

        update_music_play(music_to_play)

    def on_audio_loader(_):
        audio.play()

    def on_audio_state_changed(event: AudioStateChangeEvent):
        audio_duration = audio.get_duration()

        if event.state == AudioState.COMPLETED:
            update_play_button(is_play=False)
            update_current_time(0)
            update_end_time(0, audio_duration)
            update_progress_time(0, audio_duration)

        page.pubsub.send_all_on_topic('play_music_state', event.state)

    def on_audio_position_changed(_):
        audio_current_position = audio.get_current_position()
        audio_duration = audio.get_duration()

        if audio_current_position and audio_current_position > 0:
            update_current_time(audio_current_position)
            update_end_time(audio_current_position, audio_duration)
            update_progress_time(audio_current_position, audio_duration)

    def on_progress_time_seek(event: ControlEvent):
        audio.seek(int(float(event.data)))
        audio.resume()

    def on_progress_time_change(_):
        audio.pause()

    def on_volume_change(event: ControlEvent):
        volume = round(event.control.value, 2)

        update_volume_icon(volume)

        audio.volume = volume
        audio.update()

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

    def update_music_play(music_to_play: dict):
        audio.src = music_to_play.get('filename')

        update_music_info(music_to_play)
        update_play_button(is_play=True)
        update_musics_queue(music_to_play)

        page.update()

    def update_musics_queue(music_to_play: dict):
        nonlocal musics_queue

        if music_to_play in musics_list:
            index = musics_list.index(music_to_play)
            print(f'\n{index}')

            prev_music = musics_list[index - 1]
            next_music = musics_list[index + 1]

            musics_queue = { 'prev_music': prev_music, 'next_music': next_music }

    def update_current_time(audio_current_position: int):
        current_time.value = format_time(audio_current_position)
        current_time.update()

    def update_end_time(audio_current_position: int, audio_duration: int):
        new_time = audio_duration - audio_current_position
        end_time.value = format_time(new_time)
        end_time.update()

    def update_progress_time(current_position: int, end_position: int):
        progress_time.value = current_position
        progress_time.max = end_position

        progress_time.update()

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

        music_cover.update()

    def update_play_button(is_play: bool):
        if is_play:
            button_play.visible = False
            button_pause.visible = True
        else:
            button_play.visible = True
            button_pause.visible = False

        page.update()

    def update_volume_icon(volume: float):
        if volume >= 0.02 and volume <= 0.44:
            button_volume.icon = Icons.VOLUME_DOWN
        elif volume >= 0.45:
            button_volume.icon = Icons.VOLUME_UP
        else:
            button_volume.icon = Icons.VOLUME_OFF
        button_volume.update()

    audio = Audio(
        src='none',
        volume=0.5,
        balance=0,
        on_loaded=on_audio_loader,
        on_state_changed=on_audio_state_changed,
        on_position_changed=on_audio_position_changed,
    )

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
        icon=Icons.PLAY_ARROW,
        icon_color=Colors.GREY_900,
        icon_size=30,
        bgcolor=Colors.WHITE,
        hover_color=Colors.TRANSPARENT,
        visible=True,
        on_click=on_play_music
    )

    button_pause = IconButton(
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
        icon_color=Colors.WHITE,
        hover_color=Colors.TRANSPARENT,
        highlight_color=Colors.with_opacity(
            0.1,
            Colors.GREY_600
        ),
    )

    button_repeat = IconButton(
        icon=Icons.REPEAT,
        icon_color=Colors.WHITE,
        hover_color=Colors.TRANSPARENT,
        highlight_color=Colors.with_opacity(
            0.1,
            Colors.GREY_600
        ),
    )

    button_volume = IconButton(
        icon=Icons.VOLUME_UP,
        icon_color=Colors.WHITE,
        hover_color=Colors.TRANSPARENT,
        highlight_color=Colors.with_opacity(
            0.1,
            Colors.GREY_600
        ),
        on_click=on_volume_mute
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
                                    icon=Icons.SKIP_NEXT,
                                    icon_color=Colors.WHITE,
                                    icon_size=28,
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
                                Slider(
                                    min=0,
                                    max=1,
                                    value=0.5,
                                    width=120,
                                    label='{value}',
                                    active_color=Colors.RED_ACCENT_200,
                                    inactive_color=Colors.GREY_800,
                                    on_change=on_volume_change
                                )
                            ],
                        )
                    ]
                )
            ]
        )
    )

    page.overlay.append(audio)

    page.pubsub.subscribe_topic('play_music', on_play_music_subscribe)

    return player
