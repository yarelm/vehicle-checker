package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"

	"github.com/jung-kurt/gofpdf"
	"github.com/sendgrid/sendgrid-go"
	"github.com/sendgrid/sendgrid-go/helpers/mail"
)

type Request struct {
	Text string
}

func main() {

	log.Print("starting server...")
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

func handler(w http.ResponseWriter, r *http.Request) {
	var req Request

	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	log.Printf("req %+v", req)

	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.AddPage()
	pdf.SetFont("Arial", "B", 6)

	pdf.CellFormat(190, 7, req.Text, "0", 0, "CM", false, 0, "")

	err = pdf.OutputFileAndClose("hello.pdf")
	if err != nil {
		panic(err)
	}

	sendEmail("hello.pdf")
	w.WriteHeader(http.StatusOK)

	// fileBytes, err := ioutil.ReadFile("hello.pdf")
	// if err != nil {
	// 	panic(err)
	// }

	// w.WriteHeader(http.StatusOK)
	// w.Header().Set("Content-Type", "application/octet-stream")
	// w.Write(fileBytes)
}

func sendEmail(pdfFileName string) {
	log.Println("sending email...")

	from := mail.NewEmail(os.Getenv("FROM_NAME"), os.Getenv("FROM_EMAIL"))
	subject := "Sending with Twilio SendGrid is Fun"
	to := mail.NewEmail("Example User", os.Getenv("TO_EMAIL"))
	plainTextContent := "and easy to do anywhere, even with Go"
	htmlContent := "<strong>and easy to do anywhere, even with Go</strong>"
	message := mail.NewSingleEmail(from, subject, to, plainTextContent, htmlContent)
	client := sendgrid.NewSendClient(os.Getenv("SENDGRID_API_KEY"))

	a_pdf := mail.NewAttachment()
	dat, err := ioutil.ReadFile(pdfFileName)
	if err != nil {
		fmt.Println(err)
	}
	encoded := base64.StdEncoding.EncodeToString([]byte(dat))
	a_pdf.SetContent(encoded)
	a_pdf.SetType("application/pdf")
	a_pdf.SetFilename(pdfFileName)
	a_pdf.SetDisposition("attachment")
	message.AddAttachment(a_pdf)

	response, err := client.Send(message)
	if err != nil {
		log.Println(err)
	} else {
		fmt.Println(response.StatusCode)
		fmt.Println(response.Body)
		fmt.Println(response.Headers)
	}

}
