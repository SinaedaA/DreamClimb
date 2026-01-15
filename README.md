# DreamClimb 🧗

A climbing route recommendation system for Fontainebleau bouldering areas.

## Features
- Web scraper for bleau.info
- PostgreSQL database with 300+ sectors
- FastAPI backend with filtering (based on boulder grades, styles/tags, sectors)
- React frontend (in progress) -- Learning JS now to replace this part entirely with my code and design

## COLLECTING DATA OF ASCENTS
In order to implement personalized recommendations, I need data of actual ascents from climbers. If you have climbed in Fontainebleau and would like to contribute your ascent data, please fill out this [short questionnaire](https://dreamclimb-survey.vercel.app/). Your data will be anonymized and used solely for the purpose of improving the recommendation system. It will help train machine learning models to better understand climbing preferences and patterns.
Thank you for helping to make DreamClimb a reality!

## Future Features
- Add user database (user info; gender, height, span), with ascent logging.
- Ascent logs + user info will enable boulder recommendations to other users, based on their own ascents.
- Enable community-powered boulder descriptor tags (_e.g._ people can add descriptor tags, such as 'heel-hooky', 'toe-hooky', 'reachy moves' etc, and users can vote on them if they agree)
- Add beta-links to boulders

## Contact
Feel free to reach out if you have ideas, or want to collaborate on this project. It's really a passion/learning project for now, but I do strive to create something useful for the community 🌟
