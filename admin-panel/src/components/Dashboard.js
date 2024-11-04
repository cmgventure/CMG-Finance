// src/components/Dashboard.js
import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import Categories from './Categories';

const { Header, Content, Footer } = Layout;

function Dashboard({ setAuthToken }) {
  const [selectedMenu, setSelectedMenu] = useState('categories');

  const handleLogout = () => {
    setAuthToken(null);
    localStorage.removeItem('authToken');
  };

  return (
    <Layout>
      <Header>
        <Menu theme="dark" mode="horizontal" selectedKeys={[selectedMenu]}>
          <Menu.Item key="categories" onClick={() => setSelectedMenu('categories')}>
            Categories
          </Menu.Item>
          <Menu.Item key="logout" onClick={handleLogout} style={{ float: 'right' }}>
            Logout
          </Menu.Item>
        </Menu>
      </Header>
      <Content style={{ padding: '20px' }}>
        {selectedMenu === 'categories' && <Categories />}
      </Content>
      <Footer style={{ textAlign: 'center' }}>Admin Panel ©2023</Footer>
    </Layout>
  );
}

export default Dashboard;









// // src/components/Dashboard.js
// import React from 'react';
// import { Layout, Menu } from 'antd';
//
// const { Header, Content, Footer } = Layout;
//
// function Dashboard({ setAuthToken }) {
//   const handleLogout = () => {
//     setAuthToken(null);
//     localStorage.removeItem('authToken');
//   };
//
//   return (
//     <Layout>
//       <Header>
//         <Menu theme="dark" mode="horizontal">
//           <Menu.Item key="1">Records</Menu.Item>
//           {/* Add more menu items as needed */}
//           <Menu.Item key="logout" onClick={handleLogout} style={{ float: 'right' }}>
//             Logout
//           </Menu.Item>
//         </Menu>
//       </Header>
//       <Content style={{ padding: '20px' }}>
//         {/* Your content goes here */}
//       </Content>
//       <Footer style={{ textAlign: 'center' }}>Admin Panel ©2023</Footer>
//     </Layout>
//   );
// }
//
// export default Dashboard;



// // src/components/Dashboard.js
// import React from 'react';
// import { Layout, Menu } from 'antd';
// import RecordList from './RecordList';
//
// const { Header, Content, Footer } = Layout;
//
// function Dashboard() {
//   return (
//     <Layout>
//       <Header>
//         <Menu theme="dark" mode="horizontal">
//           <Menu.Item key="1">Records</Menu.Item>
//           {/* Add more menu items as needed */}
//         </Menu>
//       </Header>
//       <Content style={{ padding: '20px' }}>
//         <RecordList />
//       </Content>
//       <Footer style={{ textAlign: 'center' }}>
//         Admin Panel ©2023
//       </Footer>
//     </Layout>
//   );
// }
//
// export default Dashboard;
