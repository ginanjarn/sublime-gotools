# Sublime Text 3 plugin

## What
This code is modification from gocode sublime plugin.

## Feature
* Autocompletion with `gocode`
* Documentation with `godef` and `go doc`
* Format code with following option: [goreturns]
* Analysis with `go vet` and `golint`
* Rename with `gorename`
* Tagging struct with `gomodifytags`

## Requirement
Set golang binary and golang app binary in your PATH

Required package
```
go get github.com/mdempsky/gocode
go get github.com/rogpeppe/godef
go get github.com/sqs/goreturns
go get golang.org/x/lint/golint
go get golang.org/x/tools/cmd/gorename
```