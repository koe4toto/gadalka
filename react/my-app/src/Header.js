import './App.css';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Box from '@mui/material/Box';
import { Auth } from './hoc/RequireAuth'

function Header() {

    const auth = Auth()

    if (auth) {
        return (
                <Box sx={{ width: '100%', bgcolor: 'background.paper' }}>
                    <nav aria-label="secondary mailbox folders">
                        <List>
                            <ListItem disablePadding>
                                <ListItemButton href="/">
                                    <ListItemText primary="Главная" />
                                </ListItemButton>
                            </ListItem>
                            <ListItem disablePadding>
                                <ListItemButton component="a" href="/login">
                                    <ListItemText primary="Логин" />
                                </ListItemButton>
                            </ListItem>
                        </List>
                    </nav>
                </Box>
        );
    }

    return (
            <Box sx={{ width: '100%', bgcolor: 'background.paper' }}>
                <nav aria-label="secondary mailbox folders">
                    <List>
                        <ListItem disablePadding>
                            <ListItemButton href="/">
                                <ListItemText primary="Главная" />
                            </ListItemButton>
                        </ListItem>
                            <ListItem disablePadding>
                                <ListItemButton component="a" href="/area">
                                    <ListItemText primary="Предметные области 2" />
                                </ListItemButton>
                            </ListItem>
                        <ListItem disablePadding>
                            <ListItemButton component="a" href="/login">
                                <ListItemText primary="Логин" />
                            </ListItemButton>
                        </ListItem>
                    </List>
                </nav>
            </Box>
  );
}

export default Header; 
