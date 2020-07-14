# Sublime Text 3 plugin for golang

# What

This code is modification from gocode sublime plugin.

# Feature

* Autocompletion with `gocode`
* Documentation with `godef` and `go doc`
* Format code with following option: [goreturns]
* Analysis with `go vet` and `golint`
* Rename with `gorename`
* Tagging struct with `gomodifytags`

# Requirement

Required package
```
go get github.com/mdempsky/gocode
go get github.com/rogpeppe/godef
go get github.com/sqs/goreturns
go get golang.org/x/lint/golint
go get golang.org/x/tools/cmd/gorename
```

# Troubleshoot

1. Follow install instruction from [golang.org](https://golang.org/doc/install).
2. Install [required package](#requirement) defined above.

> Notice
> Set `go` binary and `go/bin`(if you in posix) or `go\bin`(if you in windows) in your `PATH`.