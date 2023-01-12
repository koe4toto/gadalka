import { Navigate } from 'react-router-dom';

const Auth = () => {
	const url = 'http://127.0.0.1:5000/api/logout'
	fetch(
		url,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json'
			}
		}
	)
		.then((response) => {
			if (response.status === 400) {
				console.log('400');
			} else {
				console.log(response.status);
				console.log('200');
			}
		})

	return true
} 

const RequireAuth = ({ children }) => {
	const auth = Auth()

	if (!auth) {
		return <Navigate to='/login'/>
	}

	return children
}

export { RequireAuth, Auth }