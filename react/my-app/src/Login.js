import './App.css';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useForm } from "react-hook-form";

function Login() {

    // обработка формы
    const { register, handleSubmit} = useForm();
    const onSubmit = data => console.log(data);

    return (
        <div className='App'>
            <Card sx={{ padding: 2 }}>
                <CardContent>
                    <form
                        noValidate
                        onSubmit={handleSubmit(onSubmit)}
                    >
                        <Typography variant="h2">Вход</Typography>
                        <TextField
                            required
                            variant="standard"
                            margin="normal"
                            fullWidth
                            id="login"
                            label="Логин"
                            name="email"
                            autoFocus
                            {...register("login")}
                        />
                        <br />
                        <TextField
                            required
                            variant="standard"
                            margin="normal"
                            fullWidth
                            name="password"
                            label="Пароль"
                            type="password"
                            id="password"
                            {...register("pass", { required: true })}
                        />
                        <br />
                        <br />
                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            color="primary"
                        >
                            Войти
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
  );
}

export default Login; 
