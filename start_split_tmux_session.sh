#!/bin/bash

SESSION_NAME=WRITE_YOUR_SESSION_NAME_HERE
tmux new-session -d -s $SESSION_NAME
tmux split-window -h
tmux send-keys -t 0 '/path/to/first/executable' Enter
tmux send-keys -t 1 '/path/to/second/executable' Enter
tmux attach-session -t $SESSION_NAME

