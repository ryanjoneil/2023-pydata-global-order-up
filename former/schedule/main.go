package main

import (
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"os"
	"regexp"
	"strings"
	"time"
)

var ODH = map[string]float64{
	"morning": 3.0,
	"midday":  4.0,
	"evening": 5.0,
	"night":   3.0,
}

var START = map[string]string{
	"morning": "07:00",
	"midday":  "11:00",
	"evening": "15:00",
	"night":   "19:00",
}

var END = map[string]string{
	"morning": "10:59",
	"midday":  "14:59",
	"evening": "18:59",
	"night":   "22:59",
}

func main() {
	var in input
	if err := json.NewDecoder(os.Stdin).Decode(&in); err != nil {
		panic(err)
	}

	newYork, err := time.LoadLocation("America/New_York")
	if err != nil {
		panic(err)
	}

	solution := in.Solutions[0]

	blocks := []forecast{}
	for _, block := range solution {
		if block.Date == os.Args[1] {
			blocks = append(blocks, block)
		}
	}

	out := output{}

	dates := []string{}
	seen := map[string]bool{}

	for _, block := range blocks {
		if !seen[block.Date] {
			dates = append(dates, block.Date)
			seen[block.Date] = true
		}

		start, err := time.ParseInLocation(
			"2006-01-02 15:04",
			fmt.Sprintf("%s %s", block.Date, START[block.Block]),
			newYork,
		)
		if err != nil {
			panic(err)
		}
		end, err := time.ParseInLocation(
			"2006-01-02 15:04",
			fmt.Sprintf("%s %s", block.Date, END[block.Block]),
			newYork,
		)
		if err != nil {
			panic(err)
		}

		out.RequiredWorkers = append(
			out.RequiredWorkers,
			requiredWorkers{
				Start: start.Format(time.RFC3339),
				End:   end.Format(time.RFC3339),
				Count: int(math.Round(block.Forecast / ODH[block.Block])),
			},
		)
	}

	for i := 0; i < 100; i++ {
		shifts := []shift{}
		for _, date := range dates {
			if rand.Float64() < 0.25 {
				continue
			}
			start := rand.Intn(17) + 7
			end := rand.Intn(17) + 7
			if start > end {
				start, end = end, start
			}
			startS, err := time.ParseInLocation(
				"2006-01-02 15:04",
				fmt.Sprintf("%s %d:00", date, start),
				newYork,
			)
			if err != nil {
				panic(err)
			}

			endS, err := time.ParseInLocation(
				"2006-01-02 15:04",
				fmt.Sprintf("%s %d:59", date, end),
				newYork,
			)
			if err != nil {
				panic(err)
			}

			shifts = append(shifts, shift{
				Start: startS.Format(time.RFC3339),
				End:   endS.Format(time.RFC3339),
			})
		}

		if len(shifts) < 1 {
			continue
		}

		out.Workers = append(out.Workers, worker{
			Availability: shifts,
			ID:           workerID(),
		})
	}

	json.NewEncoder(os.Stdout).Encode(out)
}

type input struct {
	Solutions [][]forecast
}

type forecast struct {
	Date     string // 2018-11-15
	Block    string // morning
	Forecast float64
}

type output struct {
	Workers         []worker          `json:"workers"`
	RequiredWorkers []requiredWorkers `json:"required_workers"`
}

type worker struct {
	Availability []shift `json:"availability"`
	ID           string  `json:"id"`
}

type shift struct {
	Start string `json:"start"`
	End   string `json:"end"`
}

type requiredWorkers struct {
	Start string `json:"start"`
	End   string `json:"end"`
	Count int    `json:"count"`
}

var adjectives = []string{"Recalcitrant", "Beneficent", "Flabbergasted", "Loquacious", "Mellifluous", "Cantankerous", "Effervescent", "Quixotic", "Gregarious", "Lugubrious", "Obstreperous", "Perspicacious", "Rambunctious", "Sesquipedalian", "Vivacious", "Whimsical", "Zany", "Astonishing", "Bombastic", "Cacophonous", "Dapper", "Ebullient", "Farcical", "Gibbous", "Hapless", "Ineffable", "Jocular", "Kaleidoscopic", "Lachrymose", "Munificent", "Nebulous", "Omnipotent", "Pernicious", "Querulous", "Rapscallion", "Supercilious", "Turbulent", "Ubiquitous", "Vainglorious", "Wanderlust", "Xenophilic", "Yawning", "Zealous", "Aberrant", "Bucolic", "Cryptic", "Delirious", "Enigmatic", "Frivolous", "Ghastly"}
var animals = []string{"Lemur", "Hippopotamus", "Platypus", "Sloth", "Armadillo", "Kangaroo", "Penguin", "Otter", "Meerkat", "Wombat", "Koala", "Chameleon", "Pangolin", "Ostrich", "Flamingo", "Narwhal", "Toucan", "Aardvark", "Porcupine", "Walrus", "Capuchin Monkey", "Bush Baby", "Giraffe", "Okapi", "Red Panda", "Fennec Fox", "Axolotl", "Tarsier", "Sugar Glider", "Quokka", "Blobfish", "Peacock", "Mandrill", "Proboscis Monkey", "Dik-dik", "Jerboa", "Alpaca", "Flying Squirrel", "Sea Otter", "Manatee", "Kakapo", "Binturong", "Tapir", "Guinea Pig", "Hedgehog", "Star-Nosed Mole", "Turtle", "Chinchilla", "Naked Mole Rat"}

func toSlug(s string) string {
	slug := strings.ToLower(s)
	reg := regexp.MustCompile("[^a-z0-9-]+")
	slug = reg.ReplaceAllString(slug, "-")
	return strings.Trim(slug, "-")
}

var seenIDs = map[string]bool{}

func workerID() string {
	for {
		adjective := adjectives[rand.Intn(len(adjectives))]
		animal := animals[rand.Intn(len(animals))]
		id := toSlug(fmt.Sprintf("%s %s", adjective, animal))
		if !seenIDs[id] {
			seenIDs[id] = true
			return id
		}
	}
}
