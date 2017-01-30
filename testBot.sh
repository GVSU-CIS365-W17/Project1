#! /bin/bash

#Board size:
boardSize="30 30"

#Number of games per bot:
numTests=10

#Path to MyBot:
myPath="MyBot.py"

#Path to test bot directory:
testPath="testBots"

#Maximum number of parallel simulations. As bot complexity increases
#it may be necessary to decrease this to prevent timeouts
maxThreads=12

numBots=$(ls $testPath/*Bot.py | wc -l)

#Create report header
printf "%15s%15s%15s\n" "Bot Name" "Win Percent" "Average Moves" > report
echo "=============================================" >> report

#Initialize loop variables
testsRun=0

printf "\rRunning Tests...%d%%" "$((100*$testsRun/($numBots*$numTests)))"
for Bot in $testPath/*Bot.py
do
	n=0
	numWins=0
	sumMoves=0

	#Get Bot name
	s=${Bot#*/}
	botName=${s%%.*}

	# while [ "$n" -lt "$numTests" ]; do
	while (( n < numTests )); do
		numThreads=0
		# while [ "$numThreads" -lt "$maxThreads" ]; do
		while (( (n < numTests) && ( numThreads < maxThreads ) )); do
			./halite -q -d "$boardSize" "python3 $myPath" "python3 $Bot" > "temp$n" &

			#Increment loop counter
			((n+=1))
			((testsRun+=1))
			((numThreads+=1))
		done
		wait
		printf "\rRunning Tests...%d%%" "$((100*$testsRun/($numBots*$numTests)))"
	done
	# while [ "$n" -lt "$numTests" ]; do
	# 	./halite -q -d "$boardSize" "python3 $myPath" "python3 $Bot" > "temp$n" &
	#
	# 	#Increment loop counter
	# 	((n+=1))
	# 	((testsRun+=1))
	# done
	#
	# #Wait for background processes to finish
	# wait

	printf "\rRunning Tests...%d%%" "$((100*$testsRun/($numBots*$numTests)))"

	#Collate results
	for result in temp*
	do
		#Read in results
		line=$(cat $result | grep -e '^1 ?*')
		arr=($line)

		#Print win or loss, collect results
		if [ "${arr[1]}" -eq "1" ]; then
			((numWins+=1))
		fi
		((sumMoves+=${arr[2]}))
	done

	#Calculate win percent and average moves
	let winPercent=numWins*100/numTests
	let avgMoves=sumMoves/numTests
	printf "%15s%14d%%%15d\n" "$botName" "$winPercent" "$avgMoves" >> report
done

printf "\n"

rm temp*
rm *.hlt

cat report
