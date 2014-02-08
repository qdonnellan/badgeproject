# badgeproject

The purpose of this project was simple - I wanted an alternative to the traditional gradebook that would allow my students to see what skills/competencies they had learned without the stress/ridiculousness of traditional grades.

## Features
### Badges
Each badge was attached to a specific prodecure/competency that the student should complete. The awarding of the badge was very boolean - either they completed it or not.

![badges](https://trello-attachments.s3.amazonaws.com/52f5434f608c36344c97f6e8/52f544f99fabf09f1b8ca907/12b577f52eea408f6c82f12867b98f8a/Screen_Shot_2014-02-07_at_2.37.51_PM.png) 

### Checkpoints
Instead of "assignments", I would assign checkpoints. The checkpoints contain many badges, and the percent complete of the checkpoint is the grade I would assign students once the checkpoint date had come to pass (since I still needed SOME grades our school's official gradebook)

![checkpoint1](https://trello-attachments.s3.amazonaws.com/52f5434f608c36344c97f6e8/52f544f99fabf09f1b8ca907/a8be33c72502a54742ad8d27f8e7eaf0/Screen_Shot_2014-02-07_at_2.40.10_PM.png)

![checkpoint2](https://trello-attachments.s3.amazonaws.com/52f5434f608c36344c97f6e8/52f544f99fabf09f1b8ca907/62e01fda123475e71f254cabc1f26613/Screen_Shot_2014-02-07_at_2.40.41_PM.png)

### Lessons Learned

I supposed I didn't quick learn this lesson when I deployed qCalculus a year previously - managing a webapp while teaching full-time is incredibly hard work. I simply ran out of time to maintain the badgeproject like I wanted to. 

Also, without much knowledge in javascript, the client-side implementation of this app is incredibly slow. Each time I click a button to award a badge it fires an ajax request to the server which the rest of the page has to wait for before refreshing status bars, etc. This project was the tipping point in my refusual to learn javascript/front-end frameworks. After I took some time off from badgeproject I committed myself to learning knockout.js