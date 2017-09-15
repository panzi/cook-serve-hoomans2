CC=gcc
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
POSIX_CFLAGS=$(COMMON_CFLAGS) -pedantic -Wno-gnu-zero-variadic-macro-arguments -fdiagnostics-color
CFLAGS=$(COMMON_CFLAGS)
ARCH_FLAGS=

CSH2_OBJ=$(BUILDDIR_BIN)/game_maker.o \
         $(BUILDDIR_BIN)/png_info.o \
         $(BUILDDIR_BIN)/csh2_patch_def.o \
         $(patsubst %.c,%.o,$(wildcard $(BUILDDIR_SRC)/csh2_*_data.c))

DMP_OBJ=$(BUILDDIR_BIN)/gmdump.o \
        $(BUILDDIR_BIN)/game_maker.o \
        $(BUILDDIR_BIN)/png_info.o

INF_OBJ=$(BUILDDIR_BIN)/gminfo.o \
        $(BUILDDIR_BIN)/game_maker.o \
        $(BUILDDIR_BIN)/png_info.o

UPD_OBJ=$(BUILDDIR_BIN)/gmupdate.o \
        $(BUILDDIR_BIN)/game_maker.o \
        $(BUILDDIR_BIN)/png_info.o

EXT_DEP=

ifeq ($(TARGET),win32)
	CC=i686-w64-mingw32-gcc
	ARCH_FLAGS=-m32
	BINEXT=.exe
else
ifeq ($(TARGET),win64)
	CC=x86_64-w64-mingw32-gcc
	ARCH_FLAGS=-m64
	BINEXT=.exe
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

.PHONY: all clean cook_serve_hoomans2 gmdump gmupdate patch setup pkg build_sprites

# keep intermediary files (e.g. csh2_patch_def.c) to
# do less redundant work (when cross compiling):
.SECONDARY:

all: cook_serve_hoomans2 gmdump gmupdate gminfo

cook_serve_hoomans2: $(BUILDDIR_BIN)/cook_serve_hoomans2$(BINEXT)

gmdump: $(BUILDDIR_BIN)/gmdump$(BINEXT)

gminfo: $(BUILDDIR_BIN)/gminfo$(BINEXT)

gmupdate: $(BUILDDIR_BIN)/gmupdate$(BINEXT)

setup:
	mkdir -p $(BUILDDIR_BIN) $(BUILDDIR_SRC)

patch: $(BUILDDIR_BIN)/cook_serve_hoomans2$(BINEXT)
	$<

build_sprites:
	scripts/build_sprites.py sprites $(BUILDDIR_SRC)

pkg: VERSION=$(shell git describe --tags)
pkg: $(BUILDDIR_BIN)/utils-for-advanced-users-$(VERSION)-$(TARGET).zip $(EXT_DEP) cook_serve_hoomans2

macpkg: VERSION=$(shell git describe --tags)
macpkg: $(BUILDDIR_BIN)/cook_serve_hoomans2_$(VERSION)_mac.zip

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

$(BUILDDIR_SRC)/csh2_patch_def.h: $(wildcard sprites/*/*.png) scripts/build_sprites.py
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

$(BUILDDIR_BIN)/cook_serve_hoomans2$(BINEXT): $(BUILDDIR_SRC)/csh2_patch_def.h $(CSH2_OBJ)
	$(CC) $(ARCH_FLAGS) $(CSH2_OBJ) -o $@

$(BUILDDIR_BIN)/gmdump$(BINEXT): $(DMP_OBJ)
	$(CC) $(ARCH_FLAGS) $(DMP_OBJ) -o $@

$(BUILDDIR_BIN)/gminfo$(BINEXT): $(INF_OBJ)
	$(CC) $(ARCH_FLAGS) $(INF_OBJ) -o $@

$(BUILDDIR_BIN)/gmupdate$(BINEXT): $(UPD_OBJ)
	$(CC) $(ARCH_FLAGS) $(UPD_OBJ) -o $@

clean: VERSION=$(shell git describe --tags)
clean:
	rm -f \
		$(BUILDDIR_SRC)/csh2_*_data.c \
		$(BUILDDIR_SRC)/csh2_patch_def.h \
		$(BUILDDIR_SRC)/csh2_patch_def.c \
		$(BUILDDIR_BIN)/patch_game.o \
		$(BUILDDIR_BIN)/cook_serve_hoomans2.o \
		$(BUILDDIR_BIN)/gmdump.o \
		$(BUILDDIR_BIN)/gminfo.o \
		$(BUILDDIR_BIN)/gmupdate.o \
		$(BUILDDIR_BIN)/game_maker.o \
		$(BUILDDIR_BIN)/png_info.o \
		$(BUILDDIR_BIN)/cook_serve_hoomans2$(BINEXT) \
		$(BUILDDIR_BIN)/gmdump$(BINEXT) \
		$(BUILDDIR_BIN)/gminfo$(BINEXT) \
		$(BUILDDIR_BIN)/gmupdate$(BINEXT) \
		$(BUILDDIR_BIN)/README.txt \
		$(BUILDDIR_BIN)/cook_serve_hoomans2.command \
		$(BUILDDIR_BIN)/open_with_cook_serve_hoomans2.command \
		$(BUILDDIR_BIN)/cook_serve_hoomans2_$(VERSION)_mac.zip \
		$(BUILDDIR_BIN)/utils-for-advanced-users-$(VERSION)-$(TARGET).zip
