# alpaca-fetch

Rotating alpaca photos for `fastfetch` on macOS.

The project keeps a small local cache (20 images by default), rotates the
image on every shell start, and refreshes the cache in the background when
the network is available. Images are downloaded from Wikimedia Commons,
center-cropped to a square JPEG, and never block terminal startup once the
cache has been populated.

## Install

```sh
./install.sh
```

The installer creates `~/.local/bin/alpaca-fetch` and adds one guarded line to
`~/.zshrc`. Open a new terminal or run `source ~/.zshrc`.

## Commands

```sh
alpaca-fetch                 # print the next cached image path
alpaca-fetch fastfetch       # render the image and system info
alpaca-fetch refresh         # force a cache refresh
alpaca-fetch status          # show cache details
```

The cache lives in `~/Library/Caches/alpaca-fetch` and can be removed safely.

## Terminal support

Actual inline images require a terminal image protocol. iTerm2 uses the iTerm
protocol, Kitty and WezTerm use Kitty graphics. Other terminals still get the
improved fastfetch information layout, but cannot display a normal bitmap
inline without a terminal-specific image protocol.
