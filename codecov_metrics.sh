#!/usr/bin/env sh
EXIT_CODE=0

echo "mode: set" > coverage.txt
export SERVICE_ENV=test

# for directory in `go list ./...`; do
#   go test -coverpkg=./... -coverprofile=profile.out $directory

#   if [ $? != 0 ]; then
#     EXIT_CODE=1
#   fi

#   if [ -f profile.out ] && [ $EXIT_CODE == 0 ]; then
#     cat profile.out | grep -v "mode:\|_ffjson.go" >> coverage.txt
#     rm profile.out
#   fi
# done

# if [ $EXIT_CODE != 0 ]; then
#   exit $EXIT_CODE
# fi

# if [ -n "$CODECOV_TOKEN" ]; then
#   curl -s https://codecov.io/bash | bash
#   rm coverage.txt
# else
#   go tool cover -func=coverage.txt
# fi