# 🚀 GenAi Data Profiling

## 📌 Table of Contents

- [Introduction](#-introduction)
- [Demo](#-demo)
- [Inspiration](#-inspiration)
- [What It Does](#-what-it-does)
- [How We Built It](#-how-we-built-it)
- [Challenges We Faced](#-challenges-we-faced)
- [How to Run](#-how-to-run)
- [Tech Stack](#-tech-stack)
- [Team](#-team)

## 🎯 Introduction

GenAi Data Profiling is an AI-powered solution that extracts regulatory rules from PDFs and applies them to transactional datasets for validation. The system leverages the DeepSeek LLM API to convert federal rules into JSON format and then checks the dataset for anomalies and rule violations.

## 🎥 Demo

- [Live Demo](#) (if applicable)
- [Video Demo](#) (if applicable)
- 📸 Screenshots:

## 💡 Inspiration

The financial industry is governed by complex regulations. Ensuring compliance with federal rules is challenging, especially with large datasets. We built this project to automate rule extraction and validation, making compliance easier and more efficient.

## 🔍 What It Does

- Extracts regulatory rules from PDF documents using DeepSeek LLM API
- Converts extracted rules into structured JSON format
- Validates transactional datasets against extracted rules
- Identifies anomalies and flags rule violations
- Provides detailed insights on detected violations

## 🛠 How We Built It

- Utilized **DeepSeek LLM API** for rule extraction
- Used **PyPDF2 library** for processing structured table data and unstructured text data from PDFs
- Processed data in two formats: **normal text** and **tabular data**
- Structured tabular data, split it into chunks, and prepared it for DeepSeek API
- Created a user prompt for DeepSeek API to extract and list rules and regulations from the text document
- Implemented **Python** for data processing
- Used **JSON** for structured rule representation
- &#x20;Created a user prompt for DeepSeek API to detect anomalies in the transactional dataset using the extracted rules

## 🚧 Challenges We Faced

- Determining a suitable library to extract both text and tabular data from PDFs
- Structuring the prompt effectively to get accurate rule extraction
- Handling API limitations as we used a free-tier DeepSeek API, leading to restrictions on the number of chunks sent
- Managing performance trade-offs between sending more chunks for accuracy and increased processing time

## ▶️ How to Run

UI:





Backend APIs:

1. Clone the repository:
   ```sh
   git clone https://github.com/ewfx/gaidp-admintars.git
   cd gaidp-admintars
   ```
2. Create a virtual environment and activate it:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Place the regulatory PDF file and transactional dataset in the input directory.
5. Run the main script:
   ```sh
   python main.py
   ```
6. View extracted rules in JSON format and validation reports in the output directory.

## 🏗 Tech Stack

- **DeepSeek LLM API** for rule extraction
- **PyPDF2** for PDF data processing
- **Python** for backend processing
- **JSON** for structured rule representation
- ReactJS, MaterialUI for building User Interface components

## 👥 Team

- Naveen Rawat
- Sharon Jain
- Nagachandra Vamsi Hebbare
- Satya Rohit Devalla

## 🤝 Contribution

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`feature-branch`).
3. Commit your changes and push to the branch.
4. Open a pull request.

## 📜 License

This project is licensed under the MIT License.


