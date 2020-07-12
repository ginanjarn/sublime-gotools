package main

import (
	"fmt"
	"log"
	"net"
	"os/exec"
	"time"
)

func terminateGocode() error {
	err := exec.Command("gocode", "exit").Run()
	if err != nil {
		return err
	}
	return nil
}

func main() {
	for {
		_, err := net.Dial("tcp", "localhost:22345")
		if err != nil {
			err1 := terminateGocode()
			log.Fatal(err1)
			log.Fatal(err)
			return
		}
		fmt.Println("alive")
		time.Sleep(2 * time.Minute)
	}
}
