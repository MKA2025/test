from mutagen import File
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TYER

class Tagger:
    @staticmethod
    def tag_file(filename, track_info):
        audio = File(filename, easy=True)
        
        if audio.tags is None:
            audio.add_tags()

        audio.tags['title'] = track_info.title
        audio.tags['artist'] = track_info.artist
        audio.tags['album'] = track_info.album
        audio.tags['tracknumber'] = str(track_info.track_number)
        audio.tags['date'] = str(track_info.year)

        audio.save()

    @staticmethod
    def tag_mp3(filename, track_info):
        audio = ID3(filename)
        audio.add(TIT2(encoding=3, text=track_info.title))
        audio.add(TPE1(encoding=3, text=track_info.artist))
        audio.add(TALB(encoding=3, text=track_info.album))
        audio.add(TRCK(encoding=3, text=str(track_info.track_number)))
        audio.add(TYER(encoding=3, text=str(track_info.year)))
        audio.save()
