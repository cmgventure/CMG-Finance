// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';

function App() {
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken'));

  useEffect(() => {
    // Update localStorage whenever authToken changes
    if (authToken) {
      localStorage.setItem('authToken', authToken);
    } else {
      localStorage.removeItem('authToken');
    }
  }, [authToken]);

  if (!authToken) {
    return <Login setAuthToken={setAuthToken} />;
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard setAuthToken={setAuthToken} />} />
      </Routes>
    </Router>
  );
}

export default App;



// // src/App.js
// import React, { useState } from 'react';
// import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
// import Login from './components/Login';
// import Dashboard from './components/Dashboard';
//
// function App() {
//   const [authToken, setAuthToken] = useState(null);
//
//   if (!authToken) {
//     return <Login setAuthToken={setAuthToken} />;
//   }
//
//   return (
//     <Router>
//       <Routes>
//         <Route path="/" element={<Dashboard />} />
//         {/* Add more routes as needed */}
//       </Routes>
//     </Router>
//   );
// }
//
// export default App;



// // src/App.js
// import React, { useState } from 'react';
// import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
// import Login from './components/Login';
// import Dashboard from './components/Dashboard';
//
// function App() {
//   const [authToken, setAuthToken] = useState(null);
//
//   if (!authToken) {
//     return <Login setAuthToken={setAuthToken} />;
//   }
//
//   return (
//     <Router>
//       <Switch>
//         <Route path="/" component={Dashboard} />
//       </Switch>
//     </Router>
//   );
// }
//
// export default App;

//
// import logo from './logo.svg';
// import './App.css';
//
// function App() {
//   return (
//     <div className="App">
//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Edit <code>src/App.js</code> and save to reload.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }
//
// export default App;
