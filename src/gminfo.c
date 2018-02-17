#include "game_maker.h"
#include "csd2_find_archive.h"

#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <limits.h>

static void gm_print_info(const struct gm_index *index, FILE *out) {
	fprintf(out, "Offset       Size             Type      Index Info\n");
	for (; index->section != GM_END; ++ index) {
		fprintf(out, "0x%010" PRIXPTR " 0x%010" PRIXPTR " --- %-9s -----",
			(size_t)index->offset,
			index->size,
			gm_section_name(index->section));

		switch (index->section) {
			case GM_AUDO:
			case GM_TXTR:
				fprintf(out, " %" PRIuPTR " entries\n", index->entry_count);
				for (size_t entry_index = 0; entry_index < index->entry_count; ++ entry_index) {
					const struct gm_entry *entry = &index->entries[entry_index];
					fprintf(out, "0x%010" PRIXPTR " 0x%010" PRIXPTR "     %-9s %5" PRIuPTR,
						(size_t)entry->offset,
						entry->size,
						gm_typename(entry->type),
						entry_index);

					if (index->section == GM_TXTR) {
						fprintf(out, " %4" PRIuPTR " x %-4" PRIuPTR,
							entry->meta.txtr.width,
							entry->meta.txtr.height);
					}
					fprintf(out, "\n");
				}
				break;

			default:
				fprintf(out, "\n");
				break;
		}
	}
}

int main(int argc, char *argv[]) {
	int status = 0;
	FILE *game = NULL;
	struct gm_index *index = NULL;
	const char *gamename = NULL;
	char pathbuf[PATH_MAX];

	if (argc > 2) {
		fprintf(stderr, "*** usage: %s [archive]\n", argv[0]);
		goto error;
	}

	if (argc > 1) {
		gamename = argv[1];
	}
	else {
		if (csd2_find_archive(pathbuf, PATH_MAX) < 0) {
			fprintf(stderr, "*** ERROR: Couldn't find %s file.\n", CSH2_GAME_ARCHIVE);
			goto error;
		}
		gamename = pathbuf;
		printf("Found archive: %s\n", gamename);
	}

	game = fopen(gamename, "rb");
	if (!game) {
		perror(gamename);
		goto error;
	}

	index = gm_read_index(game);
	if (!index) {
		perror(gamename);
		goto error;
	}

	gm_print_info(index, stdout);

	goto end;

error:
	status = 1;

end:
	if (game) {
		fclose(game);
		game = NULL;
	}

	if (index) {
		gm_free_index(index);
		index = NULL;
	}

#ifdef GM_WINDOWS
	printf("Press ENTER to continue...");
	getchar();
#endif

	return status;
}
