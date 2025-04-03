import './App.css';
import Chatbot from './components/Chatbot'

function App() {
  return (
    <div className="App">
      <h2>Welcome to ScheduleFlyBot!</h2>
      <h4>Please send a message to start interacting with the chatbot.</h4>
      <br></br>
      <Chatbot />
    </div>
  );
}

export default App;
