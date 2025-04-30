# Library App - Book Management System

A modern, full-stack web application for book enthusiasts to discover, manage, and organize their reading collection. Built with Flask, JavaScript, and Docker, this application provides a smooth experience for book management with real-time search capabilities and user authentication.

## Project Overview

This application serves as a comprehensive book management system that allows users to:
- Search and explore books using the Open Library API
- Create and manage personal book lists
- Save favorite books
- Sort and filter book collections
- Access a responsive, modern user interface
- Manage user accounts with role-based authentication

## Requirements Fulfillment

### Technical Requirements
- ✅ Full-stack web application architecture
- ✅ Docker containerization for easy deployment
- ✅ PostgreSQL database integration
- ✅ RESTful API implementation
- ✅ Real-time search functionality
- ✅ User authentication and authorization
- ✅ Responsive frontend design
- ✅ Book management features (favorites, lists)

### User Experience Requirements
- ✅ Intuitive navigation
- ✅ Interactive book cards with detailed information
- ✅ User-friendly book list management
- ✅ Responsive design for all device sizes

## Team Roles

### Development Team
- **Frontend Developer**: Implemented the user interface, search functionality, and interactive features
  - **Aaron Viera, Bryan Dasilva, Najada Stroka, Eli Gerszberg**
- **Backend Developer**: Developed the API endpoints, database integration, and authentication system
  - **Johan Morillo**
- **DevOps Engineer**: Set up Docker configuration
  - **Johan Morillo**
- **Database Administrator**: Designed and implemented the database schema
  - **Johan Morillo**
- **Case Testing**: Ensure website is consistent and bug/error free
  - **Najada Stroka, Eli Gerszberg**
  

## System Documentation

### Prerequisites
- Docker Desktop
- Git
- Web browser (Chrome, Firefox, or Safari recommended)

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/xiolest1/library-app.git
   cd library-app
   ```

2. **Start Docker**
   - Launch Docker Desktop
   - Ensure Docker is running (you should see the Docker icon in your system tray)

3. **Build and Run the Application**
   ```bash
   docker-compose up --build
   ```

4. **Access the Application**
   - Open your web browser
   - Navigate to `http://localhost:5001`

### Using the Application

![index](https://github.com/user-attachments/assets/706ff540-3d1f-4038-902c-0ac38e87ba05)

#### User Registration and Login
- Able to create a new account, and view your credentials within the dashboard

![user_register](https://github.com/user-attachments/assets/889b7160-2969-4871-947b-e5228fe1c09c)
![user_dashboarrd](https://github.com/user-attachments/assets/3acbc586-8d1a-4b21-a38a-9d26729abdd7)

#### Admin and Librarian Dashboard
- Staff dashboard for managing the website. Librarians can edit books within the system and (visuals for now) would be a custom user list management system where they control the custom book lists of users since it would be a public list to share to others.

#### Searching for Books
- Search system, able to filter out the search query, real-time respond and use filters to narrow down your search

![image](https://github.com/user-attachments/assets/16b58a1d-d4af-4c45-980c-18d37c4505f0)


#### Managing Book Lists
- User can manage a custom book list, able to create/edit/delete the system and will be consistent with the database. No two users share a custom list.
   
![new_list](https://github.com/user-attachments/assets/6fb086f2-6717-48d6-a4b9-b12214ec0dca)
![new_list2](https://github.com/user-attachments/assets/7a845aee-77a9-4528-9d3d-8c9738800ee6)
![new_list3](https://github.com/user-attachments/assets/ed3f4fea-64d7-40cc-b919-4e485573cf3c)
![new_list4](https://github.com/user-attachments/assets/74d50b4c-2ea7-4ef1-9efe-3568d0e95cc3)


### Troubleshooting

#### Common Issues
1. **Application not starting**
   - Ensure Docker is running
   - Check if port 5001 is available
   - Try rebuilding with `docker-compose up --build --force-recreate`

2. **Search not working**
   - Check your internet connection
   - Verify the Open Library API is accessible
   - Clear browser cache and refresh

3. **Login issues**
   - Ensure you're using the correct credentials
   - Try resetting your password
   - Clear browser cookies if problems persist

## Testing

The project includes comprehensive test cases covering:
- Unit tests for backend functionality
- Integration tests for API endpoints
- Frontend component testing
- End-to-end user flow testing

Run tests using:
```bash
docker-compose run backend pytest
docker-compose run frontend npm test
```


