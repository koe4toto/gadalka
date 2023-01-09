import './App.css';
import Login from './Login'
import Main from './Main';
import Header from './Header'
import {
    BrowserRouter as Router,
    Routes,
    Route
} from 'react-router-dom';


function App() {
    return (
        <Router>
            <Header />
            <Routes>
                <Route exact path="/" element={<Main />} />
                <Route path="/login" element={<Login />} />
            </Routes>
        </Router>
  );
}

export default App; 
