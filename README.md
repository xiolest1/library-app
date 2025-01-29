# library-app

README with pictures: https://docs.google.com/document/d/1TComLTDT7_nlRTwX1d4b0DieoFSk7Xvfv8QtmADhe-k/edit?usp=sharing

<h1>Softwares & Tools to Download</h1>

- Docker (Both Windows and MacOS)
  - https://www.docker.com/products/docker-desktop/
  
- Git: (Windows only link)
  - https://git-scm.com/downloads
  
- The project github
  - https://github.com/xiolest1/library-app/tree/main

<h2>MacOS Setup Steps</h2>

- Open terminal, check if Git is downloaded with the command:
```git -version```

- If its not, download Git here

```/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"```

 **Move onto step 1 of windows setup to finish the rest of the setup**

<h2>Windows Setup Steps</h2> 

**Step 1**

- Open up git’s terminal
    - (For Windows: type in git bash in search bar in the taskbar)
    - (For MacOS: your terminal you used previously is fine)

- Change directory to your desktop (you can save it anywhere you like, desktop is just an example)

```cd  onedrive/desktop```  

- Clone the repository with the command:
  
```git clone https://github.com/xiolest1/library-app.git```

---

**Step 2**

- Open up Docker, leave it running in the background
    -  (login with your github account or email associated with github)
  
---
**Step 3:**
- In terminal, change directory into the library-app folder

    - You can view files with the command: ```ls```
  
    - Here you should see the backend folder, frontend folder and docker-compose.yaml file
  
        - the docker-compose.yaml file is how you get the web-app up and running w/ database
      
- To build the application, and have it running, type in the command:
```docker-compose up --build```

- Open up your browser and type in “localhost:5001” 
---
