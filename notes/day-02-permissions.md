## 3. File Permissions with chmod

I used `chmod` to understand how Linux controls whether a script can be executed.

I first checked the permissions of my script:

```ls -l permission-test.sh```

The permissions were:

```-rw-r--r-- 1 atrim atrim 78 Aug 29 22:36 permission-test.sh```

There was no `x` permission, so I tried to run the script:

```./permission-test.sh```

Linux returned:

```./permission-test.sh: Permission denied```

This showed that the file existed and could be read, but it could not be executed because it did not have execute permission.

I then added execute permission:

```chmod +x permission-test.sh```

I checked the permissions again:

```ls -l permission-test.sh```

The permissions changed to:

```-rwxr-xr-x 1 atrim atrim 78 Aug 29 22:36 permission-test.sh```

The `x` permission was now present.

I ran the script again:

```./permission-test.sh```

This time it worked:

```Permission test works```

## What I learned

chmod changes the permissions of a file.

The `+x` option adds execute permission, while `-x` removes it.

When the script did not have execute permission, Linux gave the actual error:

`./permission-test.sh: Permission denied`

After adding execute permission with `chmod +x`, the script could run normally.

The important thing I learned was that having a script file does not automatically mean Linux allows it to be executed. The file needs the appropriate execute permission.