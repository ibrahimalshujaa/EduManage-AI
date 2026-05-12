print("Starting import check...")
import os
import sqlite3
print("Importing Flask...")
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
print("Importing Werkzeug...")
from werkzeug.utils import secure_filename
print("Importing local modules...")
from database import DB_PATH
print("Importing AI model...")
from ai_model import predict_student_performance
print("Importing Reports generator...")
from reports_generator import generate_pdf_report
print("All imports successful.")
