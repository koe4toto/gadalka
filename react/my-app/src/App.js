import './App.css';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';


function App() {
    return (
        <div className='App'>
            <Card sx={{ padding: 2 }}>
                <CardContent>
                    <Typography variant="h2" gutterBottom>Вход</Typography>
                    <TextField fullWidth id="standard-basic" label="Логин" variant="standard" margin="normal" />
                    <br />
                    <TextField fullWidth id="standard-password-input" label="Пароль" type="password"
                            autoComplete="current-password" variant="standard" margin="normal"/><br /><br />
                    <Button variant="contained">Войти</Button>
                </CardContent>
            </Card>
        </div>
  );
}

export default App; 
