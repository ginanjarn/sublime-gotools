# Sublime Text 3 plugin

## What
This code is modification from gocode sublime plugin.

## Feature
* Autocompletion with `gocode`
* Format code with following option: [goreturns]
* Analysis with `go vet` and `golint`

## Requirement
Set golang binary and golang app binary in your PATH

Required package
* gocode : autocompletion
>`go get -u github.com/stamblerre/gocode`
* goreturns : auto format and clean imports
>`go get -u github.com/sqs/goreturns`
* keepalive : shutdown `gocode` daemon while **sublime text** closed
>`go get github.com/ginanjarn/sublime-gotools`