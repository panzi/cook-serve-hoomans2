Cook, Serve, Hoomans! 2!!
=========================

In [one of her streams](http://www.twitch.tv/feliciaday/v/4517425?t=02h19m22s)
Felicia Day said she wishes she could put the faces of her fans on the customers
in [Cook, Serve, Delicious!](http://store.steampowered.com/app/247020/), so I
made [a "mod"](https://github.com/panzi/cook-serve-hoomans) that does just that.

Since then Cook, Serve, Delicious! 2!! was released and so I started making a
mod for that, too, just in case Felicia or Ryon want to stream that again some
day (and for fun).

I still need more pictures of hoomans (fans), so send them in! They don't need
to be photos if you rather just want your avatar or a drawing to be used. In any
case don't let your elbows stick out to the side so the picture will fit into
one of the available slots. Help from someone who is better with Photoshop/GIMP
would also be nice.

Setup
-----

Download the latest release from the [releases page](https://github.com/panzi/cook-serve-hoomans2/releases)
and double click `Cook-Serve-Hoomans-2.exe`. It should automatically find
the installation path of Cook, Serve, Delicious! 2!! and patch the game archive.
If everything went well you should see something like this:

![](http://panzi.github.io/cook-serve-hoomans2/img/patch_success.png)

Just press enter and you are done.

To be on the safe side this patch creates a backup of the game archive (if none
exist already). The backup will be placed in the same folder as the game archive
(`data.win` on Windows and `game.unx` on Linux) and will be called
`data.win.backup` on Windows and `game.unx.backup` on Linux. If you want to
remove the patch simply delete `data.win`/`game.unx` and rename the backup file.
Under Windows you might need to disable hiding of file name extensions in order
to be able to rename that file.

Another way to undo the mod is simply to verify the game file integrity with
Steam, which will detect the modification and re-download the game.

### In case that didn't work

In case `Cook-Serve-Hoomans-2.exe` couldn't automatically find the game
archive file you can pass it manually. First find `data.win` from your Cook,
Serve, Delicious! 2!! installation. Under Windows `data.win` can usually be
found at one of these or similar locations:

```
C:\Program Files\Steam\steamapps\common\CookServeDelicious2\data.win
C:\Program Files (x86)\Steam\steamapps\common\CookServeDelicious2\data.win
```

Under Linux it would be:

```
~/.local/share/Steam/SteamApps/common/CookServeDelicious2/assets/game.unx
~/.steam/steam/SteamApps/common/CookServeDelicious2/assets/game.unx
```

I don't have a Mac so I don't know where it's there and I can't provide a binary
for Mac anyway. (I don't use Windows either, but it is easily possible to cross
compile a Windows binary under Linux.)

Then simply drag and drop `data.win` onto `Cook-Serve-Hoomans-2.exe`:

![](http://panzi.github.io/cook-serve-hoomans2/img/open_with_cook_serve_hoomans.png)

If everything went well you should see the same dialog as above. Just press
enter and you are done.

Advanced Usage
--------------

If you can handle the shell there are the binaries: `gmdump.exe` and
`gmupdate.exe`. Use the first to dump all compiled sprites and sound files from
a Game Maker archive into a directory. After you edited those files you can
use the second program to update the archive.

If you don't explicitely pass the game archive to these two programs they try to
find it themselves and if you don't pass a directory to them they will use the
current working directory. So just executing them without any arguments in the
working directory of your texture files is enough.

**WARNING:** `gmdump.exe` will overwrite any existing texture files without asking.
So pay attention on where you execute this program.

### Windows Users

For Windows users that don't know/want to use the shell: Simple create a new
directory, then drag and drop this directory onto `gmdump.exe`, change the images
that you want to change and delete the others, and finally drop the same directory
onto `gmupdate.exe`.

Build From Source
-----------------

(For advanced users and software developers only.)

In case you want to build this patching tool yourself download the source and
simply run these commands in the source folder:

```
make setup
make -j`nproc`
```

If you want to cross-compile for another platform you can run one of these
commands:

```
make TARGET=linux32
make TARGET=linux64
make TARGET=win32
make TARGET=win64
```

Always make sure that the folder `build/$TARGET` exists before you run `make`.
You can do this simply by running `make TARGET=$TARGET setup`.

Finally you can run the patch by typing:

```
make patch
```

How It Works
------------

Cook, Serve, Delicious! 2!! uses [Game Maker](http://www.yoyogames.com/studio)
from YoYo Games. At first I didn't bother reverse engineering the archive file
format of this game engine, but because the file size of the replacement sprite
got bigger than the file size of the original I had to reverse engineer at least
a bit so I could rewrite the archive properly (instead of just overwriting the
proportion of the archive containing the sprite).

This program understands the overall structure of Game Maker archives, the
detailed structure of the TXTR and AUDO sections, and some parts of the SPRT and
TPAG sections. TXTR and AUDO are the last two sections in the archive, so when
the TXTR section needs resizing absolute offsets in this section and the
following section (AUDO) need to be adjusted. There don't seem to be any offsets
to parts of those sections in other places.

The SPRT and TPAG sections contain the coordinates of the sprites inside of the
textures. During compilation this information is used to generate the new
texture files and during patching this is used to verify that the patched game
archive is compatible with the textures that will be written into the game
archive.

All I know about this file format is documented in [fileformat.md](fileformat.md).
Note that this file format differs from Cook, Serve, Delicious! 1 in some ways,
so see also: https://github.com/panzi/cook-serve-hoomans/blob/master/fileformat.md

I don't know what will happen when there is a game update. Will the updater
corrupt the archive, bail because the file isn't what it expects it to be or
simply revert the patch? Your guess is as good as mine. In any case this program
creates a `data.win.backup` file which you can use in case the game stops
working. Just remove `data.win` and rename `data.win.backup` to `data.win`.

Because Felicia uses Windows and one cannot assume the availability of any sane
scripting language (like Python) on an arbitrary Windows installation I wrote
this patch as a self contained C program. Cross compiling simple C/C++ programs
for Windows under Linux is easy.

However, it is very very cumbersome to cross compile stuff for Mac under Linux
(the setup still requires access to a Mac and an Apple developer account), so I
can't provide a Mac binary. I could rewrite everything in Python (Mac, just like
most Linux distributions, actually comes with Python pre-installed), but I only
do this if there is any demand for it.
