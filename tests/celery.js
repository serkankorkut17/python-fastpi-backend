// const axios = require('axios');

// async function makeGetRequest(a, b) {
//     try {
//         const response = await axios.get('http://localhost:8000/test', {
//             params: { a, b }
//         });
//         console.log('Response data:', response.data);
//     } catch (error) {
//         console.error('Error making GET request:', error);
//     }
// }

// // Example usage
// makeGetRequest(5, 10);

const fetch = require('node-fetch');

async function makeGetRequest(a, b) {
    try {
        const response = await fetch(`http://localhost:8000/test?a=${a}&b=${b}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Response data:', data);
    } catch (error) {
        console.error('Error making GET request:', error);
    }
}

// Example usage
makeGetRequest(5, 10);
