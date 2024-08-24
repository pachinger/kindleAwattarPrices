import io
import json
import logging
import threading
import plotly.graph_objects as go
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import time

import requests
from flask import Flask, send_file

app = Flask(__name__)

def generate_image():
    try:
        # Contacting the API and getting the JSON data
        url = "https://api.awattar.at/v1/marketdata"
        logging.info("Getting data from awattar API at " + url)
        response = requests.get(url)
        data = response.json()

        logging.info("Data received successfully")

        # Parsing JSON data
        prices = [(entry["start_timestamp"], entry["marketprice"]) for entry in data["data"]]

        # Converting market price to cent per kWh and applying adjustments
        prices = [(timestamp, price / 10 * 1.03 + 1.5) for timestamp, price in prices]

        # Calculating VAT
        prices_with_vat = [(timestamp, price * 1.20) for timestamp, price in prices]

        # Extracting timestamps for the next 24 hours
        current_time = datetime.now()
        end_time = current_time + timedelta(hours=24)
        timestamps = [timestamp for timestamp, _ in prices if current_time <= datetime.fromtimestamp(timestamp / 1000) <= end_time]

        # Extracting prices for the next 24 hours
        hourly_prices = [price for timestamp, price in prices_with_vat if current_time <= datetime.fromtimestamp(timestamp / 1000) <= end_time]

        logging.info("Data processing successful")
        logging.info(timestamps)
        logging.info(hourly_prices)

        # Calculate midpoints between consecutive timestamps
        midpoints = [(timestamps[i] + timestamps[i+1]) / 2 for i in range(len(timestamps) - 1)]
        # Add a dummy value at the beginning and end to cover the full range
        midpoints.insert(0, timestamps[0] - (timestamps[1] - timestamps[0]) / 2)
        midpoints.append(timestamps[-1] + (timestamps[-1] - timestamps[-2]) / 2)

        # Convert midpoints to human-readable date-time strings (HH:MM format)
        x_labels = [datetime.fromtimestamp(timestamp / 1000).strftime('%H:%M') for timestamp in timestamps]
        # Add a dummy label at the end to cover the full range
        x_labels.append("")

        # Create figure
        fig = go.Figure()

        logging.info("Created Plotly figure successfully, adding traces")

        # Add traces
        fig.add_trace(go.Bar(x=timestamps, y=hourly_prices, marker_color='black', text=hourly_prices, textposition='outside', texttemplate='<b>%{y:.1f}</b>'))

        # Update layout
        fig.update_layout(
            title=dict(text="Awattar Strompreise", font=dict(size=30), automargin=True, yref='paper'),
            #xaxis_title='Time',
            yaxis_title='Strompreis (Cent/kWh)',
            xaxis=dict(
                #tickangle=-45,
                tickmode='array',
                tickvals=midpoints,  # Use midpoints as tickvals
                ticktext=x_labels,  # Use x_labels directly for ticktext
            ),
            yaxis=dict(gridcolor='black'),
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=30, r=30, t=30, b=30),
            height=600,
            width=800,
            annotations=[
                dict(
                    xref='paper',
                    yref='paper',
                    x=1,
                    y=1,
                    text=f'Chart created at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    showarrow=False,
                    font=dict(size=10),
                    align='right',
                )
            ]
        )

        # Convert Plotly figure to a PIL Image
        img_bytes = fig.to_image(format="png", scale=1)  # Increased scale for better quality
        pil_img = Image.open(io.BytesIO(img_bytes))

        # Rotate the image by 90 degrees
        rotated_img = pil_img.transpose(Image.ROTATE_90)

        logging.info("Image created successfully, saving it as a PNG file")

        # Save the image as a 4-bit grayscale PNG
        rotated_img = rotated_img.convert("L")  # Convert to grayscale
        rotated_img.save('awattar.png', format='PNG', bits=4)
        rotated_img.save(str(datetime.now().strftime("%Y%m%d %H%M%S"))+'.png', format='PNG', bits=4)

        return
    except Exception as e:
        logging.error(f"Error generating image: {e}")
        # Render the exception message into an image
        error_img = Image.new('RGB', (600, 800), color='white')
        draw = ImageDraw.Draw(error_img)
        font = ImageFont.load_default()
        draw.text((10, 10), f"Error generating image: {e}", fill='black', font=font)
        error_img.save('awattar.png', format='PNG', bits=4)
        return

def serve_image():

    @app.route('/awattar.png')
    def get_image():
        # log the request to make debugging easier
        logging.info(f"Received request for image at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            # serve the file awattar.png as a download

            return send_file('awattar.png', as_attachment=True)#, attachment_filename='awattar.png')
            #return send_file(img_io, mimetype='image/png')
        except Exception as e:
            logging.error(f"Error serving image: {e}")
            return f"Error serving image: {e}", 500





if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('awattar.log'), logging.StreamHandler()])
    logging.info("Starting the Awattar API Visualizer")
    # Start the Flask app in a thread
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000}).start()
    #app.run(host='localhost', port=5000)
    app.logger.info("Flask app started successfully on http://localhost:5000/")
    generate_image()
    app.logger.info("Image generated successfully")
    serve_image()
    app.logger.info("Entering sleep loop")
    while True:
        current_hour = datetime.now().hour
        #if current_hour == 1 or current_hour == 13: # Generate a new image only at 1 AM and 1 PM
        generate_image()
        app.logger.info("Sleeping for 1 hour, good night!")
        time.sleep(3600)  # Sleep for 1 hour