package main

import (
	"io"
	"log"
	"os"
)

func main() {
	var input string
	if len(os.Args) == 2 {
		input = os.Args[1]
	} else if len(os.Args) == 1 {
		input = "-"
	}
	if input == "-" {
		if _, err := io.Copy(os.Stdout, os.Stdin); err != nil {
			log.Fatal(err)
		}
	} else {
		f, err := os.Open(input) // read
		if err != nil {
			log.Fatal(err)
		}

		if _, err := io.Copy(os.Stdout, f); err != nil {
			log.Fatal(err)
		}
	}

}

