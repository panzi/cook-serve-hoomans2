#include "csd2_find_archive.h"
#include "game_maker.h"

#include <stdio.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include <stdlib.h>

#if defined(GM_WINDOWS)
#	include <windows.h>

#define CSH2_DATA_WIN_PATH "\\steamapps\\common\\CookServeDelicious2\\data.win"

struct reg_path {
	HKEY    hKey;
	LPCTSTR lpSubKey;
	LPCTSTR lpValueName;
};

static char *get_path_from_registry(HKEY hKey, LPCTSTR lpSubKey, LPCTSTR lpValueName) {
	HKEY hSubKey = 0;
	DWORD dwType = REG_SZ;
	DWORD dwSize = 0;
	char *path = NULL;

	if (RegOpenKeyEx(hKey, lpSubKey, 0, KEY_QUERY_VALUE, &hSubKey) != ERROR_SUCCESS) {
		goto error;
	}

	if (RegQueryValueEx(hSubKey, lpValueName, NULL, &dwType, (LPBYTE)NULL, &dwSize) != ERROR_SUCCESS || dwType != REG_SZ) {
		goto error;
	}

	path = malloc(dwSize + 1);
	if (path == NULL) {
		goto error;
	}

	if (RegQueryValueEx(hSubKey, lpValueName, NULL, &dwType, (LPBYTE)path, &dwSize) != ERROR_SUCCESS || dwType != REG_SZ) {
		goto error;
	}

	goto end;

error:
	if (path != NULL) {
		free(path);
		path = NULL;
	}

end:
	if (hSubKey != 0) {
		RegCloseKey(hSubKey);
	}

	return path;
}

char *csd2_find_archive() {
	static const struct reg_path reg_paths[] = {
		// Have confirmed sigthings of these keys:
		{ HKEY_LOCAL_MACHINE, TEXT("Software\\Valve\\Steam"),              TEXT("InstallPath") },
		{ HKEY_LOCAL_MACHINE, TEXT("Software\\Wow6432node\\Valve\\Steam"), TEXT("InstallPath") },
		{ HKEY_CURRENT_USER,  TEXT("Software\\Valve\\Steam"),              TEXT("SteamPath")   },

		// All the other possible combination, just to try everything:
		{ HKEY_CURRENT_USER,  TEXT("Software\\Wow6432node\\Valve\\Steam"), TEXT("SteamPath")   },
		{ HKEY_LOCAL_MACHINE, TEXT("Software\\Valve\\Steam"),              TEXT("SteamPath")   },
		{ HKEY_LOCAL_MACHINE, TEXT("Software\\Wow6432node\\Valve\\Steam"), TEXT("SteamPath")   },
		{ HKEY_CURRENT_USER,  TEXT("Software\\Valve\\Steam"),              TEXT("InstallPath") },
		{ HKEY_CURRENT_USER,  TEXT("Software\\Wow6432node\\Valve\\Steam"), TEXT("InstallPath") },
		{ 0,                  0,                                           0                   }
	};

	for (const struct reg_path* reg_path = reg_paths; reg_path->lpSubKey; ++ reg_path) {
		char *path = get_path_from_registry(reg_path->hKey, reg_path->lpSubKey, reg_path->lpValueName);
		if (path != NULL) {
			return path;
		}
	}

	errno = ENOENT;
	return NULL;
}
#elif defined(__APPLE__)

#define CSD_STEAM_ARCHIVE "Library/Application Support/Steam/SteamApps/common/CookServeDelicious2/Cook Serve Delicious 2.app/Contents/Resources/game.ios"
#define CSD_APP_ARCHIVE   "/Applications/Cook Serve Delicious 2.app/Contents/Resources/game.ios"

char *csd2_find_archive() {
	const char *home = getenv("HOME");
	struct stat info;

	if (home) {
		char *path = GM_JOIN_PATH_EX(home, CSD_STEAM_ARCHIVE);
		if (path != NULL) {
			if (stat(path, &info) < 0) {
				if (errno != ENOENT) {
					perror(path);
				}
			}
			else if (S_ISREG(info.st_mode)) {
				return path;
			}
			free(path);
		}
	}

	if (stat(CSD_APP_ARCHIVE, &info) < 0) {
		if (errno != ENOENT) {
			perror(CSD_APP_ARCHIVE);
		}
		return NULL;
	}
	else if (S_ISREG(info.st_mode)) {
		return strdup(CSD_APP_ARCHIVE);
	}

	errno = ENOENT;
	return NULL;
}
#else // default: Linux
#include <dirent.h>

static char *find_path_ignore_case(const char *prefix, const char* const path[]) {
	char *filepath = strdup(prefix);

	if (filepath == NULL) {
		return NULL;
	}

	for (const char* const* nameptr = path; *nameptr; ++ nameptr) {
		const char* realname = NULL;
		DIR *dir = opendir(filepath);

		if (!dir) {
			if (errno != ENOENT) {
				perror(filepath);
			}
			free(filepath);
			return NULL;
		}

		for (;;) {
			errno = 0;
			struct dirent *entry = readdir(dir);
			if (entry) {
				if (strcasecmp(entry->d_name, *nameptr) == 0) {
					realname = entry->d_name;
					break;
				}
			}
			else if (errno == 0) {
				break; // end of dir
			}
			else {
				perror(filepath);
				free(filepath);
				return NULL;
			}
		}

		if (!realname) {
			closedir(dir);
			free(filepath);
			errno = ENOENT;
			return NULL;
		}

		closedir(dir);

		char *nextpath = GM_JOIN_PATH_EX(filepath, realname);
		free(filepath);

		if (nextpath == NULL) {
			return NULL;
		}

		filepath = nextpath;
	}

	return filepath;
}

char *csd2_find_archive() {
	// Steam was developed for Windows, which has case insenstive file names.
	// Therefore I can't assume a certain case and because I don't want to write
	// a parser for registry.vdf I scan the filesystem for certain names in a case
	// insensitive manner.
	static const char* const path1[] = {".local/share", "Steam", "SteamApps", "common", "CookServeDelicious2" ,"assets", "game.unx", NULL};
	static const char* const path2[] = {".steam", "Steam", "SteamApps", "common", "CookServeDelicious2", "assets", "game.unx", NULL};
	static const char* const* paths[] = {path1, path2, NULL};

	const char *home = getenv("HOME");

	if (!home) {
		errno = ENOENT;
		return NULL;
	}

	for (const char* const* const* ptr = paths; ptr; ++ ptr) {
		const char* const* path_spec = *ptr;
		char *path = find_path_ignore_case(home, path_spec);
		if (path != NULL) {
			struct stat info;

			if (stat(path, &info) < 0) {
				if (errno != ENOENT) {
					perror(path);
				}
			}
			else if (S_ISREG(info.st_mode)) {
				return path;
			}
			free(path);
		}
	}

	errno = ENOENT;
	return NULL;
}
#endif
