package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/sendgrid/sendgrid-go"
	"github.com/sendgrid/sendgrid-go/helpers/mail"
)

type VehicleDetails struct {
	VehicleID string
	Brand     string
	Model     string
	Year      string
	FrontTire string
	BackTire  string
}

type RequestVehicle struct {
	VehicleDetails
	ToEmail string
}

func main() {
	log.Print("starting server...")
	http.HandleFunc("/failure", failureHandler)
	http.HandleFunc("/", handler)

	// Determine port for HTTP service.
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
		log.Printf("defaulting to port %s", port)
	}

	// Start HTTP server.
	log.Printf("listening on port %s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}

type Failure struct {
	VehicleID string
	ToEmail   string
}

func failureHandler(w http.ResponseWriter, r *http.Request) {
	var req Failure

	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	sendEmail(fmt.Sprintf("Vehicle ID Info: %v", req.VehicleID), "There was an error :(", req.ToEmail)
	w.WriteHeader(http.StatusOK)
}

func handler(w http.ResponseWriter, r *http.Request) {
	var req RequestVehicle

	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	sendEmail(fmt.Sprintf("Vehicle ID Info: %v", req.VehicleID), fmt.Sprintf("Vehicle Info: %+v", req.VehicleDetails), req.ToEmail)
	w.WriteHeader(http.StatusOK)

}

func sendEmail(subject, text, toEmail string) {
	log.Println("sending email...")

	from := mail.NewEmail(os.Getenv("FROM_NAME"), os.Getenv("FROM_EMAIL"))
	to := mail.NewEmail("Example User", toEmail)
	message := mail.NewSingleEmail(from, subject, to, text, "")
	client := sendgrid.NewSendClient(os.Getenv("SENDGRID_API_KEY"))

	response, err := client.Send(message)
	if err != nil {
		log.Println(err)
	} else {
		fmt.Println(response.StatusCode)
		fmt.Println(response.Body)
		fmt.Println(response.Headers)
	}
}
