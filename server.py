from flask import Flask, render_template, request
from EmotionDetection import emotion_detector

app = Flask(__name__)

@app.route("/")
def render_index_page():
    return render_template('index.html')

@app.route("/emotionDetector")
def emotion_detector_app():
    # Get the text from the request arguments
    text_to_analyze = request.args.get('textToAnalyze')
    
    # Call the emotion detector function
    response = emotion_detector(text_to_analyze)
    
    # Extract the dominant emotion
    dominant_emotion = response['dominant_emotion']
    
    # Format the response as requested
    if dominant_emotion is None:
        return "Invalid text! Please try again!"
    
    # Create the formatted response string
    formatted_response = (
        f"For the given statement, the system response is "
        f"'anger': {response['anger']}, 'disgust': {response['disgust']}, "
        f"'fear': {response['fear']}, 'joy': {response['joy']} and "
        f"'sadness': {response['sadness']}. "
        f"The dominant emotion is <b>{dominant_emotion}</b>."
    )
    
    return formatted_response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)