#include "game_maker.h"
#include "csd2_find_archive.h"

#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <limits.h>

int main(int argc, char *argv[]) {
	int status = 0;
	const char *indir = ".";
	const char *gamename = NULL;
	char pathbuf[PATH_MAX];

	if (argc > 3) {
		fprintf(stderr, "*** usage: %s [archive] [dir]\n", argv[0]);
		goto error;
	}

	for (int i = 1; i < argc; ++ i) {
		char *arg = argv[i];
		struct stat info;

		if (stat(arg, &info) < 0) {
			perror(arg);
			goto error;
		}
		else if (S_ISDIR(info.st_mode)) {
			indir = arg;
		}
		else {
			gamename = arg;
		}
	}

	if (gamename == NULL) {
		if (csd2_find_archive(pathbuf, PATH_MAX) < 0) {
			fprintf(stderr, "*** ERROR: Couldn't find %s file.\n", CSH2_GAME_ARCHIVE);
			goto error;
		}
		gamename = pathbuf;
		printf("Found archive: %s\n", gamename);
	}

	// patch the archive
	if (gm_patch_archive_from_dir(gamename, indir) != 0) {
		fprintf(stderr, "*** ERROR: Error patching archive: %s\n", strerror(errno));
		goto error;
	}
	
	printf("Successfully pached game.\n");

	goto end;

error:
	status = 1;

end:

#ifdef GM_WINDOWS
	printf("Press ENTER to continue...");
	getchar();
#endif

	return status;
}
