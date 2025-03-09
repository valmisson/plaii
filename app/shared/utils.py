import os
from glob import glob
from tinytag import TinyTag

def load_music_files(start=0, limit=100):
    try:
        default_music_dirs = [
            os.path.join(os.path.expanduser('~'), 'Music')
        ]
        audio_type = ['*.mp3', '*.wav', '*.flac', '*.aac', '*.ogg']

        music_files = []

        for dir in default_music_dirs:
            for type in audio_type:
                files = glob(
                    os.path.join(dir, '**', type),
                    recursive=True
                )
                for file in files:
                    music_files.append(file)

        return music_files[start:start+limit]
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
