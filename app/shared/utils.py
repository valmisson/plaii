import os
from re import match
from glob import glob
from tinytag import TinyTag

def load_music_files(music_dirs) -> list[TinyTag]:
    try:
        audio_type = ['*.mp3', '*.wav', '*.flac', '*.aac', '*.ogg']

        music_files = []

        for dir in music_dirs:
            for type in audio_type:
                files = glob(
                    os.path.join(dir, '**', type),
                    recursive=True
                )
                for file in files:
                    music_metadata = load_music_metadata(file=file)

                    music_files.append({
                        'title': get_music_title(music_metadata),
                        'artist': get_music_artist(music_metadata),
                        'album': get_music_album(music_metadata),
                        'duration': format_time(music_metadata.duration),
                        'filename': music_metadata.filename,
                        'parent_folder': dir
                    })

        return music_files
    except Exception as err:
        print(f'Erro ao carregar musicas: {err}')

def load_music_metadata(file: str, with_image=False):
    try:
        audio = TinyTag.get(file, image=with_image)

        return audio
    except Exception as err:
        print(f'Error ao ler metadados: {err}')

def get_music_title(music: TinyTag) -> str:
    title = music.title if music.title else \
        os.path.splitext(os.path.basename(music.filename))[0]

    return f'{music.track}. {title}' if music.track else title

def get_music_artist(music: TinyTag) -> str:
    return music.artist if music.artist else 'Artista desconhecido'

def get_music_album(music: TinyTag) -> str:
    return music.album if music.album else 'Álbum desconhecido'

def format_time(time: float) -> str:
    hours = int(time // 3000)
    minutes = int((time % 3600) // 60)
    seconds = int(time % 60)

    if hours > 0:
        return f'{hours}:{minutes:02d}:{seconds:02d}'
    else:
        return f'{minutes:02d}:{seconds:02d}'

def sort_by(list: list[dict], key: str):
    def sort_key(text: str):
        regex = match(r'(\d+)', text)
        if regex:
            return (0, int(regex.group(0)), text)
        return (1, text)

    return sorted(list, key=lambda i: sort_key(i[key]))
