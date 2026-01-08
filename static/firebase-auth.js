// Firebase Configuration for Price Alert App
// Initialize Firebase with your project config

const firebaseConfig = {
  apiKey: "AIzaSyCd2loVUb73eUyjzzaIi_rOTnR_6VIZWAk",
  authDomain: "tahcchat-147ed.firebaseapp.com",
  projectId: "tahcchat-147ed",
  storageBucket: "tahcchat-147ed.firebasestorage.app",
  messagingSenderId: "99674078177",
  appId: "1:99674078177:web:9f1909955b8be2fe15f0a0",
  measurementId: "G-Z6HW7M2ZSK"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const analytics = firebase.analytics();

// Auth reference
const auth = firebase.auth();
const googleProvider = new firebase.auth.GoogleAuthProvider();

// Sign in with Google
function signInWithGoogle() {
  return auth.signInWithPopup(googleProvider)
    .then((result) => {
      const user = result.user;
      console.log('Google sign-in successful:', user);
      return user;
    })
    .catch((error) => {
      console.error('Google sign-in error:', error);
      throw error;
    });
}

// Sign in with email/password
function signInWithEmail(email, password) {
  return auth.signInWithEmailAndPassword(email, password)
    .then((userCredential) => {
      const user = userCredential.user;
      console.log('Email sign-in successful:', user);
      return user;
    })
    .catch((error) => {
      console.error('Email sign-in error:', error);
      throw error;
    });
}

// Sign up with email/password
function signUpWithEmail(email, password, username) {
  return auth.createUserWithEmailAndPassword(email, password)
    .then(async (userCredential) => {
      const user = userCredential.user;
      
      // Update profile with username
      await user.updateProfile({
        displayName: username
      });
      
      console.log('Email sign-up successful:', user);
      return user;
    })
    .catch((error) => {
      console.error('Email sign-up error:', error);
      throw error;
    });
}

// Sign out
function signOut() {
  return auth.signOut()
    .then(() => {
      console.log('Sign-out successful');
    })
    .catch((error) => {
      console.error('Sign-out error:', error);
    });
}

// Get current user
function getCurrentUser() {
  return auth.currentUser;
}

// Get ID token for backend verification
async function getIdToken() {
  const user = auth.currentUser;
  if (user) {
    return await user.getIdToken();
  }
  return null;
}

// Listen to auth state changes
function onAuthStateChanged(callback) {
  auth.onAuthStateChanged(callback);
}

// Check if user is authenticated
function isAuthenticated() {
  return auth.currentUser !== null;
}
