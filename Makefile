CC=gcc
BINNAME=cook_serve_hoomans2
# stupid github limits file names unnecesarrily
WIN_BINNAME=Cook-Serve-Hoomans-2
BINEXT=
TARGET=$(shell uname|tr '[A-Z]' '[a-z]')$(shell getconf LONG_BIT)
BUILDDIR=build
BUILDDIR_BIN=$(BUILDDIR)/$(TARGET)
BUILDDIR_SRC=$(BUILDDIR)/src
INCLUDE=-I$(BUILDDIR_SRC) -Isrc
COMMON_CFLAGS=-Wall -Werror -Wextra -std=gnu11 $(INCLUDE)
ifeq ($(DEBUG),ON)
	COMMON_CFLAGS+=-g -DDEBUG
else
	COMMON_CFLAGS+=-O2
endif
POSIX_CFLAGS=$(COMMON_CFLAGS) -pedantic -fdiagnostics-color
CFLAGS=$(COMMON_CFLAGS)
ARCH_FLAGS=
WINDRES=windres
INKSCAPE=inkscape
CONVERT=convert
ARCHIVE=$(shell ./scripts/find_archive.py)

CSH2_OBJ=$(BUILDDIR_BIN)/cook_serve_hoomans2.o \
         $(BUILDDIR_BIN)/csd2_find_archive.o \
         $(BUILDDIR_BIN)/game_maker.o \
         $(BUILDDIR_BIN)/png_info.o \
         $(BUILDDIR_BIN)/csh2_patch_def.o

CSH2_DATA_OBJ=$(patsubst $(BUILDDIR_SRC)/%.c,$(BUILDDIR_BIN)/%.o,$(wildcard $(BUILDDIR_SRC)/csh2_*_data.c))

DMP_OBJ=$(BUILDDIR_BIN)/gmdump.o \
        $(BUILDDIR_BIN)/csd2_find_archive.o \
        $(BUILDDIR_BIN)/game_maker.o \
        $(BUILDDIR_BIN)/png_info.o

INF_OBJ=$(BUILDDIR_BIN)/gminfo.o \
        $(BUILDDIR_BIN)/csd2_find_archive.o \
        $(BUILDDIR_BIN)/game_maker.o \
        $(BUILDDIR_BIN)/png_info.o

UPD_OBJ=$(BUILDDIR_BIN)/gmupdate.o \
        $(BUILDDIR_BIN)/csd2_find_archive.o \
        $(BUILDDIR_BIN)/game_maker.o \
        $(BUILDDIR_BIN)/png_info.o

ICONS=$(BUILDDIR_SRC)/icon_16.png \
      $(BUILDDIR_SRC)/icon_20.png \
      $(BUILDDIR_SRC)/icon_24.png \
      $(BUILDDIR_SRC)/icon_32.png \
      $(BUILDDIR_SRC)/icon_40.png \
      $(BUILDDIR_SRC)/icon_48.png \
      $(BUILDDIR_SRC)/icon_64.png \
      $(BUILDDIR_SRC)/icon_96.png \
      $(BUILDDIR_SRC)/icon_128.png \
      $(BUILDDIR_SRC)/icon_256.png

EXT_DEP=

ifeq ($(TARGET),win32)
	CC=i686-w64-mingw32-gcc
	WINDRES=i686-w64-mingw32-windres
	ARCH_FLAGS=-m32
	BINEXT=.exe
	CSH2_OBJ+=$(BUILDDIR_BIN)/resources.o
	BINNAME=$(WIN_BINNAME)
else
ifeq ($(TARGET),win64)
	CC=x86_64-w64-mingw32-gcc
	WINDRES=x86_64-w64-mingw32-windres
	ARCH_FLAGS=-m64
	BINEXT=.exe
	CSH2_OBJ+=$(BUILDDIR_BIN)/resources.o
	BINNAME=$(WIN_BINNAME)
else
ifeq ($(TARGET),linux32)
	CFLAGS=$(POSIX_CFLAGS)
	ARCH_FLAGS=-m32
else
ifeq ($(TARGET),linux64)
	CFLAGS=$(POSIX_CFLAGS)
	ARCH_FLAGS=-m64
else
ifeq ($(TARGET),darwin32)
	CC=clang
	CFLAGS=$(POSIX_CFLAGS)
	ARCH_FLAGS=-m32
	EXT_DEP=macpkg
else
ifeq ($(TARGET),darwin64)
	CC=clang
	CFLAGS=$(POSIX_CFLAGS)
	ARCH_FLAGS=-m64
	EXT_DEP=macpkg
endif
endif
endif
endif
endif
endif

.PHONY: all clean cook_serve_hoomans2 gmdump gmupdate patch setup pkg \
        build_sprites internal_make_binary icon unpatch

# keep intermediary files (e.g. csh2_patch_def.c) to
# do less redundant work (when cross compiling):
.SECONDARY:

all: cook_serve_hoomans2 gmdump gmupdate gminfo

cook_serve_hoomans2: "$(BUILDDIR_BIN)/$(BINNAME)$(BINEXT)"

gmdump: $(BUILDDIR_BIN)/gmdump$(BINEXT)

gminfo: $(BUILDDIR_BIN)/gminfo$(BINEXT)

gmupdate: $(BUILDDIR_BIN)/gmupdate$(BINEXT)

setup:
	mkdir -p $(BUILDDIR_BIN) $(BUILDDIR_SRC)

patch: "$(BUILDDIR_BIN)/$(BINNAME)$(BINEXT)"
	$<

unpatch: $(ARCHIVE).backup
	cp "$<" "$(ARCHIVE)"

build_sprites:
	scripts/build_sprites.py sprites $(BUILDDIR_SRC)

pkg: VERSION=$(shell git describe --tags)
pkg: $(BUILDDIR_BIN)/utils-for-advanced-users-$(VERSION)-$(TARGET).zip $(EXT_DEP) cook_serve_hoomans2

macpkg: VERSION=$(shell git describe --tags)
macpkg: $(BUILDDIR_BIN)/cook_serve_hoomans2_$(VERSION)_mac.zip

icon: $(BUILDDIR_SRC)/icon.ico

$(BUILDDIR_BIN)/cook_serve_hoomans2_$(VERSION)_mac.zip: \
		$(BUILDDIR_BIN)/cook_serve_hoomans2 \
		$(BUILDDIR_BIN)/cook_serve_hoomans2.command \
		$(BUILDDIR_BIN)/open_with_cook_serve_hoomans2.command \
		$(BUILDDIR_BIN)/README.txt
	mkdir -p $(BUILDDIR_BIN)/bin
	cp $(BUILDDIR_BIN)/cook_serve_hoomans2 $(BUILDDIR_BIN)/bin
	cd $(BUILDDIR_BIN); zip -r9 cook_serve_hoomans2_$(VERSION)_mac.zip \
		bin \
		cook_serve_hoomans2.command \
		open_with_cook_serve_hoomans2.command \
		README.txt
	rm -r $(BUILDDIR_BIN)/bin

$(BUILDDIR_BIN)/%.command: osx/%.command
	cp $< $@

$(BUILDDIR_BIN)/README.txt: osx/README.txt
	cp $< $@

$(BUILDDIR_BIN)/utils-for-advanced-users-$(VERSION)-$(TARGET).zip: gmdump gminfo gmupdate
	mkdir -p $(BUILDDIR_BIN)/utils-for-advanced-users-$(VERSION)-$(TARGET)
	cp \
		README.md \
		$(BUILDDIR_BIN)/gmdump$(BINEXT) \
		$(BUILDDIR_BIN)/gminfo$(BINEXT) \
		$(BUILDDIR_BIN)/gmupdate$(BINEXT) \
		$(BUILDDIR_BIN)/utils-for-advanced-users-$(VERSION)-$(TARGET)
	cd $(BUILDDIR_BIN); zip -r9 utils-for-advanced-users-$(VERSION)-$(TARGET).zip \
		utils-for-advanced-users-$(VERSION)-$(TARGET)
	rm -r $(BUILDDIR_BIN)/utils-for-advanced-users-$(VERSION)-$(TARGET)

$(BUILDDIR_SRC)/csh2_patch_def.h: $(wildcard sprites/*/*.png) scripts/build_sprites.py hoomans.csv
	scripts/build_sprites.py sprites $(BUILDDIR_SRC)

$(BUILDDIR_SRC)/csh2_patch_def.c: $(BUILDDIR_SRC)/csh2_patch_def.h

$(BUILDDIR_BIN)/csh2_patch_def.o: $(BUILDDIR_SRC)/csh2_patch_def.c src/game_maker.h
	$(CC) $(ARCH_FLAGS) $(CFLAGS) -c $< -o $@

$(BUILDDIR_BIN)/%.o: src/%.c
	$(CC) $(ARCH_FLAGS) $(CFLAGS) -c $< -o $@

$(BUILDDIR_BIN)/%.o: $(BUILDDIR_SRC)/%.c
	$(CC) $(ARCH_FLAGS) $(CFLAGS) -c $< -o $@

$(BUILDDIR_BIN)/cook_serve_hoomans2.o: \
		src/cook_serve_hoomans2.c \
		$(BUILDDIR_SRC)/csh2_patch_def.h
	$(CC) $(ARCH_FLAGS) $(CFLAGS) -c $< -o $@

# recursive make trick so $(CSH2_DATA_OBJ) is expanded for the generated C files
internal_make_binary: $(CSH2_OBJ) $(CSH2_DATA_OBJ)
	$(CC) $(ARCH_FLAGS) $(CFLAGS) $(CSH2_OBJ) $(CSH2_DATA_OBJ) -o "$(BUILDDIR_BIN)/$(BINNAME)$(BINEXT)"

"$(BUILDDIR_BIN)/$(BINNAME)$(BINEXT)": $(BUILDDIR_SRC)/csh2_patch_def.h $(CSH2_OBJ)
	$(MAKE) TARGET=$(TARGET) internal_make_binary

$(BUILDDIR_BIN)/gmdump$(BINEXT): $(DMP_OBJ)
	$(CC) $(ARCH_FLAGS) $(CFLAGS) $(DMP_OBJ) -o $@

$(BUILDDIR_BIN)/gminfo$(BINEXT): $(INF_OBJ)
	$(CC) $(ARCH_FLAGS) $(CFLAGS) $(INF_OBJ) -o $@

$(BUILDDIR_BIN)/gmupdate$(BINEXT): $(UPD_OBJ)
	$(CC) $(ARCH_FLAGS) $(CFLAGS) $(UPD_OBJ) -o $@

$(BUILDDIR_BIN)/resources.o: $(BUILDDIR_SRC)/resources.rc $(BUILDDIR_SRC)/icon.ico
	$(WINDRES) $< -o $@

$(BUILDDIR_SRC)/resources.rc: windows/resources.rc
#	iconv -f UTF-8 -t CP1250 $< -o $@
	cp $< $@

$(BUILDDIR_SRC)/icon.ico: $(ICONS)
	$(CONVERT) $(ICONS) -background transparent $@

$(ICONS): icon/raccoon.svg
	$(INKSCAPE) $< --export-width=$(patsubst $(BUILDDIR_SRC)/icon_%.png,%,$@) --export-area-page --export-png=$@

clean: VERSION=$(shell git describe --tags)
clean:
	rm -f \
		$(ICONS) \
		$(BUILDDIR_SRC)/icon.ico \
		$(CSH2_OBJ) \
		$(CSH2_DATA_OBJ) \
		$(BUILDDIR_SRC)/csh2_*_data.c \
		$(BUILDDIR_SRC)/csh2_patch_def.h \
		$(BUILDDIR_SRC)/csh2_patch_def.c \
		$(BUILDDIR_BIN)/patch_game.o \
		$(BUILDDIR_BIN)/cook_serve_hoomans2.o \
		$(BUILDDIR_BIN)/csd2_find_archive.o \
		$(BUILDDIR_BIN)/gmdump.o \
		$(BUILDDIR_BIN)/gminfo.o \
		$(BUILDDIR_BIN)/gmupdate.o \
		"$(BUILDDIR_BIN)/$(BINNAME)$(BINEXT)" \
		$(BUILDDIR_BIN)/gmdump$(BINEXT) \
		$(BUILDDIR_BIN)/gminfo$(BINEXT) \
		$(BUILDDIR_BIN)/gmupdate$(BINEXT) \
		$(BUILDDIR_BIN)/README.txt \
		$(BUILDDIR_BIN)/cook_serve_hoomans2.command \
		$(BUILDDIR_BIN)/open_with_cook_serve_hoomans2.command \
		$(BUILDDIR_BIN)/cook_serve_hoomans2_$(VERSION)_mac.zip \
		$(BUILDDIR_BIN)/utils-for-advanced-users-$(VERSION)-$(TARGET).zip
