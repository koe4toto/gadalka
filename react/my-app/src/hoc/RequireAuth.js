import { Navigate } from 'react-router-dom'

const Auth = false

const RequireAuth = ({ children }) => {

	if (!Auth) {
		return <Navigate to='/login'/>
	}

	return children
}

export { RequireAuth, Auth }