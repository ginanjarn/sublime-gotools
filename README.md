# SUBLIME-GOTOOLS
---
## FEATURE
* Code completion with `gocode-gomod`.
* Auto import packages with `goreturns` and `gofmt`.
* Code check with `go vet`

## INSTALLATION
1. Clone git repository [https://github.com/ginanjarn/sublime-gotools](https://github.com/ginanjarn/sublime-gotools) on your sublime `Packages` directory.
2. Set `GOPATH` and `GOROOT` settings in `Packages/User` named `go.sublime-settings`. (Sometimes not needed if you are in windows.)

>`go.sublime-settings`
>```json
>{
>	"GOPATH":"your/gopath",
>	"GOROOT":"your/goroot",
>}
>```

## LIMITATION
* on hover definition removed due to conflict on displaying `gocode` completion.
* manual stopping gocode daemon by `gocode-gomod exit` on your teminal or cmd

## NOTES
>If you struggling with autocompletion not displayed, remove `sublime-text-3` in `~/.config` if you are in linux or `%APPDATA%/Roaming` if you are in windows.