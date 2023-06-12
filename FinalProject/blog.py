import re

class Blog: ##[TODO] Testing of class usage and link with Blockchain
    def __init__(self):
        self.users = {}
        self.posts = []

    def make_new_post(self, username, title, content):
        if username not in self.users:
            self.users[username] = []

        post = {
            'title': title,
            'content': content,
            'author': username,
            'comments': []
        }

        self.posts.append(post)
        self.users[username].append(post)

    def comment_on_post(self, username, title, comment):
        post = self.find_post_by_title(title)
        if post:
            post['comments'].append({
                'username': username,
                'comment': comment
            })
        else:
            print("Cannot create comment. The post doesn't exist.")

    def view_all_posts(self):
        #sorted_posts = sorted(self.posts, key=lambda x: x['timestamp'])
        if not self.posts:
            print("BLOG EMPTY")
        for post in self.posts:
            print("-----")
            print(f"Title: {post['title']}")
            print(f"Author: {post['author']}")
            print(f"Content: {post['content']}")
            if post['comments']:
                print("-----")
                print("Comments:")
                for comm in post['comments']:
                    print(f"{comm['username']}: {comm['comment']}")
        print("-----")
            
    def view_user_posts(self, username):
        if self.users and username in self.users:
            user_posts = self.users[username]
            for post in user_posts:
                print(f"Title: {post['title']}")
                print(f"Content: {post['content']}")
                print("Comments:")
                for comment in post['comments']:
                    print(f"\tUsername: {comment['username']}")
                    print(f"\tComment: {comment['comment']}")
        else:
            print("NO POST")  

    def view_post_comments(self, title):
        post = self.find_post_by_title(title)
        if post:
            print(f"Title: {post['title']}")
            print(f"Content: {post['content']}")
            print("Comments:")
            for comment in post['comments']:
                print(f"\tUsername: {comment['username']}")
                print(f"\tComment: {comment['comment']}")
        else:
            print("The post doesn't exist.")

    def view_post_by_title(self, title):
        post = self.find_post_by_title(title)
        print(post)
        if post:
            print(f"Title: {post['title']}")
            print(f"Content: {post['content']}")
            print("Comments:")
            for comment in post['comments']:
                print(f"\tUsername: {comment['username']}")
                print(f"\tComment: {comment['comment']}")
        else:
            print("POST NOT FOUND")

    def find_post_by_title(self, title):
        for post in self.posts:
            if post['title'] == title:
                return post
        return None
    
    def restore_posts(self, PID):
        try:
            with open(f"restore_chain_{PID}.txt", "r") as f:
                for line in f:
                    if line == "[]":
                        return
                    else:
                        line = line.strip("()\n")
                        match = re.match(r"\[(.*?)\], (.*), (.*)", line)
                        if match:
                            user_op = match.group(1).replace("\'", "").split(", ")
                            if int(user_op[3]) == 0:
                                self.make_new_post(user_op[0], user_op[1], user_op[2])
                            else:
                                self.comment_on_post(user_op[0], user_op[1], user_op[2]) 
        except FileNotFoundError:
            return