// File: ssn_hash.go
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"flag"
	"fmt"
)

func main() {
	// ── 1. Parse command-line flags ─────────────────────────────
	ssn  := flag.String("ssn",  "", "Social Security number (digits only or with dashes)")
	salt := flag.String("salt", "", "Salt value (string)")
	flag.Parse()

	if *ssn == "" || *salt == "" {
		fmt.Println("Usage: go run ssn_hash.go -ssn=<SSN> -salt=<salt>")
		return
	}

	// ── 2. Concatenate salt and SSN ─────────────────────────────
	plain := *salt + *ssn

	// ── 3. Compute SHA-256 ─────────────────────────────────────
	sum := sha256.Sum256([]byte(plain))
	hashHex := hex.EncodeToString(sum[:])

	// ── 4. Output ───────────────────────────────────────────────
	fmt.Printf("SHA-256(salt+ssn) = %s\n", hashHex)
}
