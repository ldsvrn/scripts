# WIP: Musicolet backup tools

This is a WIP script to pull information from a Musicolet backup .zip file. 

[Musicolet](https://play.google.com/store/apps/details?id=in.krosbits.musicolet) is a free (as in beer) but closed source music player for Android. However it is completely offline, it doesn't even have the network permission. 

Even after multiple years of searching, I'm unable to find an open-source equivalent that even comes close to it in terms of functionalities.

Musicolet uses unencrypted .zip backups, however every file in the archive is BLowfish encrypted with the **hardcoded key** `JSTMUSIC_2`. Yes, it is indeed using a **HARDCODED ENCRYPTION KEY** (see [here](https://www.reddit.com/r/androidapps/comments/t9zwow/comment/i0tfpaa/)).
This key is prone to change depending on the developper mind, but since it is hardcoded (completely useless) it can always be found again. 

## Usage (WIP)
```
usage: musicolet-tools.py [-h] [-d dir] [-v] backup_path {export,print} ...

Extract information out of a Musicolet backup

positional arguments:
  backup_path        Musicolet backup .zip path
  {export,print}     Subcommands
    export           Exports playlists
    print            Print information in the terminal

options:
  -h, --help         show this help message and exit
  -d, --decrypt dir  Extracts and decrypts all files to the specified directory
  -v, --verbose      Include DEBUG level logs
```

## export
```
usage: musicolet-tools.py backup_path export [-h] (-p name | -t N | --top-time N | -f | -a) [-r csv] [-c] output

Exports playlists or favorites to m3u8 files

positional arguments:
  output               Output dir

options:
  -h, --help           show this help message and exit
  -p, --playlist name  Choose a playlist to export
  -t, --top N          Export the top N songs alltime (by listens)
  --top-time N         Export the top N songs alltime (by time)
  -f, --favorites      Export all favourites songs
  -a, --all            Export all playlists and favourites songs
  -r, --replace csv    Replace part of the path with something else, comma separated 'old,new,old2,new2', last 2 values are not required and will apply only
                       if the first replace is done, this argument can be called multiple times
  -c, --check          Check if file exists before writing it to the m3u8, test done after replace
```

## print
```
usage: musicolet-tools.py backup_path print [-h] [-f | -p name | -t N | --top-time N | -a] [--paths]

Print information in the terminal

options:
  -h, --help           show this help message and exit
  -f, --favorites      Print all favourites songs
  -p, --playlist name  Print the content of a playlist
  -t, --top N          Print top N played songs (by listens)
  --top-time N         Print top N played songs (by time)
  -a, --all-playlists  Print all playlist names
  --paths              Print paths instead of names
```