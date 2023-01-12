import './App.css';
import Login from './Login'
import Main from './Main';
import Area from './Area';
import Header from './Header'
import {
    BrowserRouter as Router,
    Routes,
    Route
} from 'react-router-dom';
import { RequireAuth } from './hoc/RequireAuth'


function App() {
    return (
        <Router>
            <Header />
            <Routes>
                <Route exact path="/" element={<Main />} />
                <Route path="/login" element={<Login />} />
                <Route path="/area" element={
                    <RequireAuth>
                        <Area />
                    </RequireAuth>
                } />    
            </Routes>
        </Router>
  );
}

export default App; 
