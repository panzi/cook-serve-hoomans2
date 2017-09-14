#ifndef COOK_SERVE_HOOMANS2_H
#define COOK_SERVE_HOOMANS2_H
#pragma once

#if defined(_WIN16) || defined(_WIN32) || defined(_WIN64)
#	define CSH2_GAME_ARCHIVE "data.win"
#elif defined(__APPLE__)
#	define CSH2_GAME_ARCHIVE "game.ios"
#else
#	define CSH2_GAME_ARCHIVE "game.unx"
#endif

#endif
