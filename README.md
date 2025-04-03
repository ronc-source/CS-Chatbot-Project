# CS-Chatbot-Project
For CSI5180 by Ronnie Charles (300072300)

Currently this repository does not have the virtual environment used for this project (rasa_chatbot_env) since the file size is above the current limit allowed. If you need access to this folder please contact me at rchar005@uottawa.ca

To run the chatbot service:
- Open the 'Project' folder and create a new terminal
- In this new terminal setup the virtual environment (rasa_chatbot_env) required
- Next create 2 terminals
- In the first terminal, run the following command to launch the REST API service that the react website will require 'rasa run --cors "*" --enable-api --debug'
- In the second terminal, run the following command to launch the action service necessary to handle custom functions 'rasa run actions'

- Next open the 'Project Website' folder and CD into the react project
- In this react directory create a new terminal and run the react service using 'npm start'
- The website should appear at your localhost and you can begin interacting with the chatbot


