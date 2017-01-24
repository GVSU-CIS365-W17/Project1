#! /bin/bash

#Board size:
boardSize="30 30"

#Number of games per bot:
numTests=1

#Path to MyBot:
myPath="MyBot.py"

#Path to test bot directory:
testPath="testBots"

numBots=$(ls $testPath/*Bot.py | wc -l)

#Create report header
printf "%15s%15s%15s\n" "Bot Name" "Win Percent" "Average Moves" > report
echo "=============================================" >> report

testsRun=0
printf "\rRunning Tests...%d%%" "$((100*$testsRun/($numBots*$numTests)))"
for Bot in $testPath/*Bot.py
do
	n=0
	numWins=0
	sumMoves=0

	while [ "$n" -lt "$numTests" ]; do
		#Run test
		./halite -q -d "$boardSize" "python3 $myPath" "python3 $Bot" > temp

		#Read in results
		line=$(cat temp | grep -e '^1 ?*')
		arr=($line)

		#Get Bot name
		s=${Bot#*/}
		botName=${s%%.*}

		#Print win or loss, collect results
		if [ "${arr[1]}" -eq "1" ]; then
			# echo "won against $botName"
			((numWins+=1))
		# else
			# echo "lost against $botName"
		fi
		((sumMoves+=${arr[2]}))

		#Increment loop counter
		((n+=1))
		((testsRun+=1))
		printf "\rRunning Tests...%d%%" "$((100*$testsRun/($numBots*$numTests)))"
	done

	#Calculate win percent and average moves
	let winPercent=numWins*100/numTests
	let avgMoves=sumMoves/numTests
	# echo "Win percent: $winPercent%"
	# echo "Average moves: $avgMoves"
	printf "%15s%14d%%%15d\n" "$botName" "$winPercent" "$avgMoves" >> report
done

printf "\n"

rm temp
rm *.hlt

cat report
