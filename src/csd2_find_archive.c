#include "csd2_find_archive.h"

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

static int get_path_from_registry(HKEY hKey, LPCTSTR lpSubKey, LPCTSTR lpValueName, char *path, size_t pathlen) {
	HKEY hSubKey = 0;
	DWORD dwType = REG_SZ;
	DWORD dwSize = pathlen;

	if (pathlen < sizeof(CSH2_DATA_WIN_PATH)) {
		return ENAMETOOLONG;
	}

	if (RegOpenKeyEx(hKey, lpSubKey, 0, KEY_QUERY_VALUE, &hSubKey) != ERROR_SUCCESS) {
		return ENOENT;
	}

	if (RegQueryValueEx(hSubKey, lpValueName, NULL, &dwType, (LPBYTE)path, &dwSize) != ERROR_SUCCESS) {
		RegCloseKey(hSubKey);
		return ENOENT;
	}

	RegCloseKey(hSubKey);

	if (dwType != REG_SZ) {
		return ENOENT;
	}
	else if (dwSize > pathlen - sizeof(CSH2_DATA_WIN_PATH)) {
		return ENAMETOOLONG;
	}

	strcat(path, CSH2_DATA_WIN_PATH);

	return 0;
}

int csd2_find_archive(char *path, size_t pathlen) {
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
		int errnum = get_path_from_registry(reg_path->hKey, reg_path->lpSubKey, reg_path->lpValueName, path, pathlen);
		if (errnum == 0) {
			return 0;
		}
		else if (errnum != ENOENT) {
			errno = errnum;
			return -1;
		}
	}

	errno = ENOENT;
	return -1;
}
#elif defined(__APPLE__)

#define CSD_STEAM_ARCHIVE "Library/Application Support/Steam/SteamApps/common/CookServeDelicious2/Cook Serve Delicious 2.app/Contents/Resources/game.ios"
#define CSD_APP_ARCHIVE   "/Applications/Cook Serve Delicious 2.app/Contents/Resources/game.ios"

int csd2_find_archive(char *path, size_t pathlen) {
	const char *home = getenv("HOME");
	struct stat info;

	if (!home) {
		return -1;
	}

	if (GM_JOIN_PATH(path, pathlen, home, CSD_STEAM_ARCHIVE) == 0) {
		if (stat(path, &info) < 0) {
			if (errno != ENOENT) {
				perror(path);
			}
		}
		else if (S_ISREG(info.st_mode)) {
			return 0;
		}
	}

	if (stat(CSD_APP_ARCHIVE, &info) < 0) {
		if (errno != ENOENT) {
			perror(path);
		}
		return -1;
	}
	else if (S_ISREG(info.st_mode)) {
		if (strlen(CSD_APP_ARCHIVE) + 1 > pathlen) {
			errno = ENAMETOOLONG;
			return -1;
		}
		strcpy(path, CSD_APP_ARCHIVE);
		return 0;
	}

	errno = ENOENT;
	return -1;
}
#else // default: Linux
#include <dirent.h>

static int find_path_ignore_case(const char *home, const char *prefix, const char* const path[], char buf[], size_t size) {
	int count = snprintf(buf, size, "%s/%s", home, prefix);
	if (count < 0) {
		return -1;
	}
	else if ((size_t)count >= size) {
		errno = ENAMETOOLONG;
		return -1;
	}

	for (const char* const* nameptr = path; *nameptr; ++ nameptr) {
		const char* realname = NULL;
		DIR *dir = opendir(buf);

		if (!dir) {
			if (errno != ENOENT) {
				perror(buf);
			}
			return -1;
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
				perror(buf);
				return -1;
			}
		}

		if (!realname) {
			closedir(dir);
			errno = ENOENT;
			return -1;
		}

		if (strlen(buf) + strlen(realname) + 2 > size) {
			errno = ENAMETOOLONG;
			return -1;
		}

		strcat(buf, "/");
		strcat(buf, realname);

		closedir(dir);
	}

	return 0;
}

int csd2_find_archive(char *path, size_t pathlen) {
	// Steam was developed for Windows, which has case insenstive file names.
	// Therefore I can't assume a certain case and because I don't want to write
	// a parser for registry.vdf I scan the filesystem for certain names in a case
	// insensitive manner.
	static const char* const path1[] = {".local/share", "Steam", "SteamApps", "common", "CookServeDelicious2" ,"assets", "game.unx", NULL};
	static const char* const path2[] = {".steam", "Steam", "SteamApps", "common", "CookServeDelicious2", "assets", "game.unx", NULL};
	static const char* const* paths[] = {path1, path2, NULL};

	const char *home = getenv("HOME");

	if (!home) {
		return -1;
	}

	for (const char* const* const* ptr = paths; ptr; ++ ptr) {
		const char* const* path_spec = *ptr;
		if (find_path_ignore_case(home, path_spec[0], path_spec + 1, path, pathlen) == 0) {
			struct stat info;

			if (stat(path, &info) < 0) {
				if (errno != ENOENT) {
					perror(path);
				}
			}
			else if (S_ISREG(info.st_mode)) {
				return 0;
			}
		}
	}

	errno = ENOENT;
	return -1;
}
#endif
