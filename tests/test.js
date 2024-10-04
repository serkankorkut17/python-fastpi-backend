const loginMutation = `
  mutation Login {
    login(username: "test", password: "password") {
      ok
      accessToken
    }
  }
`;

const createPostMutation = `
  mutation CreatePost {
    createPost(title: "a title", content: "a content") {
      ok
      postId
    }
  }
`;

// Function to send GraphQL queries
const sendGraphQLRequest = async (query, token = null) => {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch('http://0.0.0.0:8000/graphql/', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({ query })
    });

    const data = await response.json();

    if (response.ok) {
      return data.data;
    } else {
      console.error('Error:', data.errors);
      return null;
    }
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
};

// Login first to get the access token
const loginAndCreatePost = async () => {
  // Step 1: Login
  const loginData = await sendGraphQLRequest(loginMutation);
  
  if (loginData && loginData.login && loginData.login.ok) {
    const accessToken = loginData.login.accessToken;
    console.log('Login successful. Access Token:', accessToken);

    // Step 2: Use the access token to create a post
    const postData = await sendGraphQLRequest(createPostMutation, accessToken);

    if (postData && postData.createPost && postData.createPost.ok) {
      console.log('Post created successfully. Post ID:', postData.createPost.postId);
    } else {
      console.error('Failed to create post.');
    }
  } else {
    console.error('Login failed.');
  }
};

// Call the function to execute the login and create post flow
loginAndCreatePost();
