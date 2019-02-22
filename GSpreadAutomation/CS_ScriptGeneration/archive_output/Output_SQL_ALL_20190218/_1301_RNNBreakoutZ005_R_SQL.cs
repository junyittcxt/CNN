#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Xml.Serialization;
using System.IO;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.SuperDom;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.Core.FloatingPoint;
using NinjaTrader.NinjaScript.Indicators;
using NinjaTrader.NinjaScript.DrawingTools;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using MySql.Data.MySqlClient;
#endregion

// This namespace holds all strategies and is required. Do not change it.
namespace NinjaTrader.NinjaScript.Strategies
{
	public class _1301_RNNBreakoutZ005_R_SQL : Strategy
	{
        #region Variables
		// General Variables
		private List<InstrumentClass> TradedList 			= new List<InstrumentClass>();
		private List<InstrumentClass> TargetLongList		= new List<InstrumentClass>();
		private List<InstrumentClass> TargetShortList		= new List<InstrumentClass>();
		private List<InstrumentClass> CurrentLongList 		= new List<InstrumentClass>();
		private List<InstrumentClass> CurrentShortList		= new List<InstrumentClass>();
		private List<InstrumentClass> EnterLongList			= new List<InstrumentClass>();
		private List<InstrumentClass> EnterShortList		= new List<InstrumentClass>();
		private List<InstrumentClass> ExitLongList			= new List<InstrumentClass>();
		private List<InstrumentClass> ExitShortList			= new List<InstrumentClass>();
		private List<InstrumentClass> RebalIncLongList		= new List<InstrumentClass>();
		private List<InstrumentClass> RebalRedLongList		= new List<InstrumentClass>();
		private List<InstrumentClass> RebalIncShortList		= new List<InstrumentClass>();
		private List<InstrumentClass> RebalRedShortList		= new List<InstrumentClass>();
		private List<EvolutionClass> Evolution				= new List<EvolutionClass>();
		private PerformanceClass Metrics					= new PerformanceClass();
		private StateClass States							= new StateClass();
		private SessionClass SessionInfo					= new SessionClass();
		private ReportingClass Reports						= new ReportingClass();
		private RotationClass Rotation						= new RotationClass();

		private SessionIterator ThisSession;
		private DateTime ThisOpen;
		private DateTime ThisClose;

		private string StatusString;
		private string MailString;
		private string DecisionInfo;
		private string LastOrderId;

		private int TotalOvernights;
		private int OvernightsFlat;
		private int TotalBars;
		private int BarsFlat;

		private MySqlCommand Cmd			= new MySqlCommand();
		private MySqlConnection	Conn		= new MySqlConnection("Server=192.168.1.110;Database=machinelearning;Port=3306;Uid=cxtanalytics;Password=3.1415cxt");

		// Specific Functional Parameters
		private Dictionary<string, int> long_fade_count;
		private Dictionary<string, int> short_fade_count;

		private Dictionary<string, double> long_signal_value;
		private Dictionary<string, double> short_signal_value;

		private MLDictionary ShortData;
		private MLDictionary LongData;

		private List<List<double>> LongSignal;
		private List<List<double>> ShortSignal;

		// Indicators
		#endregion

		#region OnStateChange
		protected override void OnStateChange()
		{
			#region Default Parameters
			if (State == State.SetDefaults)
			{
				Description				= "Deep Learning Rotation Strategy using signals from MySQL tables (M30/15/5 Strategy Only. Main Instrument set to FX, either EURUSD or GBPUSD if not used in RefInstrument)";
				Name					= "_1301_RNNBreakoutZ005_R_SQL";

				// 1. Strategy Specific
				RefInstrument			= "NZDUSD";

				dbTableLong				= "z005b";
				dbTableShort			= "z005s";
				BuySignalThreshold 		= 0.5;
				SellSignalThreshold 	= 0.5;
				ConsecutiveSignalBars   = 9;
				OrderType				= 2;

				// 2. SQL Related
				SignalLag 				= 0;

//				 2. Optimizable

				// 3. Capital
				AllocationMethod		= 3;
				InitialCapital			= 1000000;
				LeverageFactor			= 1;
				ReinvestmentPct			= 100;
				FixedSize				= false;

				// 4. Other Presets
				MaxDailyTrades			= 0;
				MaxDailyLosses			= 0;
				MaxDailyLossPct			= 0;
				MinReentryBars			= 0;
				TimeStopBars			= 0;
				StopLossPct				= 0;
				TargetProfitPct			= 0;
				TrailStopPct			= 0;

				// 5. Sessions
				Sessions				= 0;
				S1Begin					= 0;
				S1End					= 0;
				S2Begin					= 0;
				S2End					= 0;
				S3Begin					= 0;
				S3End					= 0;
				BlockEntryTime			= 0;
				FlattenTime				= 0;
				ControlFlatten			= false;
				OutOfSessionExit		= false;
				BypassEntryFilters		= false;
				BypassTradeHalts		= false;

				// 6. Reporting
				LogDirectoryPath		= @"C:\Algos\";
				MailNotifications		= true;
				DisplayStatusBox		= false;
				BacktestSummary			= true;
				EvolutionSummary		= false;
				WriteOutput				= false;

				// 7.1. Rotation / Basic
				NumInstruments			= RefInstrument.Split(',').Length;
				NumLongs				= 0;
				NumShorts				= 0;
				TradableStartIndex		= 1;
				DecisionFrequency		= 1;
				RebalanceFrequency		= 0;
				OrderDelayBars			= 0;
				RebalanceThreshold		= 0;
				RotationInverseMode		= false;

				// 7.2. Rotation / Filters
				FilterMode				= 0;
				FilterMinSize			= 0;
				SkipTopLongs			= 0;
				SkipTopShorts			= 0;
				RotationLongFilter		= false;
				RotationShortFilter		= false;

				// 7.3. Rotation / Cutoff
				CutoffMaxSize			= 0;
				CutoffLongThreshold		= 0;
				CutoffShortThreshold	= 0;
				RotationCutoffMode		= true;
				RotationCutoffLongs		= true;
				RotationCutoffShorts	= true;

				// Strategy Property Defaults (General)
				Calculate 						= Calculate.OnBarClose;
				DaysToLoad 						= 365;
				BarsRequiredToTrade 			= 0;
				IsExitOnSessionCloseStrategy	= false;
				ExitOnSessionCloseSeconds		= 60;
				EntriesPerDirection 			= 1;
				EntryHandling 					= EntryHandling.UniqueEntries;

				SetOrderQuantity 				= SetOrderQuantity.Strategy;
				TimeInForce						= TimeInForce.Gtc;
				MaximumBarsLookBack 			= MaximumBarsLookBack.Infinite;
				StartBehavior					= StartBehavior.ImmediatelySubmit;

				// Strategy Property Defaults (Backtesting)
				OrderFillResolution        					= OrderFillResolution.Standard;
				IncludeCommission 							= true;
				Slippage									= 1;
				IsInstantiatedOnEachOptimizationIteration	= true;
				MaxProcessedEvents 							= 1000;
				IncludeTradeHistoryInBacktest				= true;
			}
			#endregion
			// Default parameters to be pushed to the UI are placed here.

			#region Instruments and Indicators
			else if (State == State.Configure)
			{
				// Secondary data series go here.
				string[] Refs = RefInstrument.Split(',');
				foreach(string o in Refs)
				{
					AddDataSeries(o.Trim(), BarsPeriods[0].BarsPeriodType, BarsPeriods[0].Value);
				}

				// Initialize indicators.

			}
			#endregion
			// Additional data series and indicators are placed here.

			#region Setup (OnStartUp)
			else if (State == State.Historical)
			{
				DoPrintAlt("##### Starting up strategy.", -1);

				// Strategy specific settings.
				long_fade_count = new Dictionary<string, int>();
				short_fade_count = new Dictionary<string, int>();
				long_signal_value = new Dictionary<string, double>();
				short_signal_value = new Dictionary<string, double>();


				// Modify culture settings for formatting.
				#region Culture Settings
	            System.Globalization.CultureInfo NewCulture 			= new System.Globalization.CultureInfo("en-us");
	            NewCulture.NumberFormat.CurrencyNegativePattern 		= 1;
	           	System.Threading.Thread.CurrentThread.CurrentCulture 	= NewCulture;
				#endregion

				// Populate class variables.
				#region Class Variables
				SessionInfo.Sessions			= Sessions;
				SessionInfo.S1Begin				= S1Begin;
				SessionInfo.S1End				= S1End;
				SessionInfo.S2Begin				= S2Begin;
				SessionInfo.S2End				= S2End;
				SessionInfo.S3Begin				= S3Begin;
				SessionInfo.S3End				= S3End;
				SessionInfo.BlockEntryTime		= BlockEntryTime;
				SessionInfo.FlattenTime			= FlattenTime;
				SessionInfo.ControlFlatten		= ControlFlatten;
				SessionInfo.OutOfSessionExit	= OutOfSessionExit;

				Metrics.FixedSize				= FixedSize;
				Metrics.ReinvestmentPct			= ReinvestmentPct;
				Metrics.InitialCapital			= InitialCapital;
				Metrics.CurrentCapital			= InitialCapital;
				Metrics.PriorCapital			= InitialCapital;
				Metrics.LeverageFactor			= LeverageFactor;
				Metrics.MaxDailyLossPct			= MaxDailyLossPct;
				Metrics.MaxDailyLosses			= MaxDailyLosses;
				Metrics.MaxDailyTrades			= MaxDailyTrades;
				Metrics.TrailStopPct			= TrailStopPct;

				States.BypassEntryFilters		= BypassEntryFilters;
				States.BypassTradeHalts			= BypassTradeHalts;
				States.HasRun					= true;
				States.StrategySetupDone		= false;
				States.SessionSetupDone			= false;
				States.OnTheCloseDone			= true;

				Reports.MailNotifications		= MailNotifications;
				Reports.BacktestSummary			= BacktestSummary;
				Reports.EvolutionSummary		= EvolutionSummary;
				Reports.WriteOutput				= WriteOutput;
				Reports.SummaryHeader			= true;
				Reports.OutputHeader			= true;

				DoPrintAlt("[Classes Setup] Setup complete.", -1);
				#endregion

				// Rotation class variables and sanity checks.
				#region Rotation Variables
				Rotation.AllocationMethod		= AllocationMethod;

				Rotation.RotationInverseMode	= RotationInverseMode;
				Rotation.NumInstruments			= NumInstruments;
				Rotation.NumLongs				= NumLongs;
				Rotation.NumShorts				= NumShorts;
				Rotation.TradableStartIndex		= TradableStartIndex;
				Rotation.DecisionFrequency		= DecisionFrequency;
				Rotation.RebalanceFrequency		= RebalanceFrequency;
				Rotation.OrderDelayBars			= OrderDelayBars;
				Rotation.RebalanceThreshold		= RebalanceThreshold;

				Rotation.RotationLongFilter		= RotationLongFilter;
				Rotation.RotationShortFilter	= RotationShortFilter;
				Rotation.FilterMode				= FilterMode;
				Rotation.FilterMinSize			= FilterMinSize;
				Rotation.SkipTopLongs			= SkipTopLongs;
				Rotation.SkipTopShorts			= SkipTopShorts;

				Rotation.RotationCutoffMode		= RotationCutoffMode;
				Rotation.RotationCutoffLongs	= RotationCutoffLongs;
				Rotation.RotationCutoffShorts	= RotationCutoffShorts;
				Rotation.CutoffMaxSize			= CutoffMaxSize;
				Rotation.CutoffLongThreshold	= CutoffLongThreshold;
				Rotation.CutoffShortThreshold	= CutoffShortThreshold;

				Rotation.FirstDecision			= true;
				Rotation.CurrentTimeSeries		= 1;

				RotationSanityChecks(Rotation);
				DoPrintAlt("[Rotation Class Setup] Setup complete, no invalid parameters.", -1);
				#endregion

				// Generate CSV paths.
				#region Logging Setup
				if (Account.Name == "Backtest")
				{
					Reports.FolderPath 	= LogDirectoryPath + @"Backtest\" + Name + @"\";

					if (Reports.BacktestSummary)
					{
						Reports.SummaryPath	= Reports.FolderPath + Instruments[0].MasterInstrument.Name + ".csv";
						Directory.CreateDirectory(Reports.FolderPath);
						System.IO.File.Delete(Reports.SummaryPath);

						DoPrintAlt("[Logging Setup] SummaryPath = " + Reports.SummaryPath, -1);
					}
					else
						DoPrintAlt("[Logging Setup] No summary logging requested.", -1);

					if (Reports.EvolutionSummary)
					{
						Reports.EvolutionPath = Reports.FolderPath + Instruments[0].MasterInstrument.Name + "_EVO.txt";
						Directory.CreateDirectory(Reports.FolderPath);
						System.IO.File.Delete(Reports.EvolutionPath);

						DoPrintAlt("[Logging Setup] EvolutionPath = " + Reports.EvolutionPath, -1);
					}
					else
						DoPrintAlt("[Logging Setup] No evolution logging requested.", -1);
				}
				else
				{
					Reports.FolderPath 	= LogDirectoryPath + @"Live\" + Name + @"\";

					Reports.SummaryPath	= Reports.FolderPath + Instruments[0].MasterInstrument.Name + ".csv";
					Reports.TradesPath	= Reports.FolderPath + @"Trades\" + Instruments[0].MasterInstrument.Name + ".csv";
					Directory.CreateDirectory(Reports.FolderPath);
					Directory.CreateDirectory(Reports.FolderPath + @"Trades\");

					DoPrintAlt("[Logging Setup] SummaryPath = " + Reports.SummaryPath, -1);
					DoPrintAlt("[Logging Setup] TradesPath = " + Reports.TradesPath, -1);

				}

				if (Reports.WriteOutput)
				{
					Reports.OutputPath	= Reports.FolderPath + @"Output\" + Instruments[0].MasterInstrument.Name + ".txt";
					Directory.CreateDirectory(Reports.FolderPath);
					Directory.CreateDirectory(Reports.FolderPath + @"Output\");

					DoPrintAlt("[Logging Setup] OutputPath = " + Reports.OutputPath, -1);
				}
				#endregion

				// Populate the instrument list.
				#region Instrument List Setup
				for (int i = Rotation.TradableStartIndex; i < (Rotation.TradableStartIndex + Rotation.NumInstruments); i++)
				{
					InstrumentClass o		= new InstrumentClass();
					o.Index					= i;
					o.Symbol				= Instruments[i].MasterInstrument.Name;

					o.HasPosition			= false;
					o.CurrentPosition		= 0;

					o.AveragePrice			= 0;
					o.StopPrice				= 0;
					o.OpenProfitLoss		= 0;
					o.OpenReturn			= 0;

					o.DecisionPrice			= 0;
					o.DecisionString		= null;

					TradedList.Add(o);
					DoPrintAlt("[Instrument List Setup] Adding " + o.Symbol, -1);
				}

				// Check for duplicates.
				TradedList = TradedList
				.GroupBy(o => o.Symbol)
				.Select(g => g.First())
				.ToList();

				if (NumInstruments > TradedList.Count)
				{
					LogError("[Instrument List Setup] Duplicates found. Please remove and restart.", true, -1);
					SetState(State.Terminated);
					return;
				}

				DoPrintAlt("[Instrument List Setup] Setup complete.", -1);
				#endregion

				// Populate the trade evolution class. Additional signals can be added here.
				#region Trade Evolution Setup
				if (Account.Name == "Backtest" && Reports.EvolutionSummary)
				{
					EvolutionClass EvoAll		= new EvolutionClass();
					EvoAll.SignalName			= "All";
					Evolution.Add(EvoAll);

					EvolutionClass EvoLong		= new EvolutionClass();
					EvoLong.SignalName			= "Long";
					Evolution.Add(EvoLong);

					EvolutionClass EvoShort		= new EvolutionClass();
					EvoShort.SignalName			= "Short";
					Evolution.Add(EvoShort);

					EvolutionClass EvoWin		= new EvolutionClass();
					EvoWin.SignalName			= "Win";
					Evolution.Add(EvoWin);

					EvolutionClass EvoLoss		= new EvolutionClass();
					EvoLoss.SignalName			= "Loss";
					Evolution.Add(EvoLoss);

					EvolutionClass EvoLongWin	= new EvolutionClass();
					EvoLongWin.SignalName		= "LongWin";
					Evolution.Add(EvoLongWin);

					EvolutionClass EvoLongLoss	= new EvolutionClass();
					EvoLongLoss.SignalName		= "LongLoss";
					Evolution.Add(EvoLongLoss);

					EvolutionClass EvoShortWin	= new EvolutionClass();
					EvoShortWin.SignalName		= "ShortWin";
					Evolution.Add(EvoShortWin);

					EvolutionClass EvoShortLoss	= new EvolutionClass();
					EvoShortLoss.SignalName		= "ShortLoss";
					Evolution.Add(EvoShortLoss);
				}
				#endregion

				// Perform session setup.
				SessionSetup(SessionInfo, States);
				ThisSession 	= new SessionIterator(BarsArray[0]);

				//Load SQL
//				Print(RefInstrument.Split(','));
				Print("Loading MySQL Tables to Custom MLDictionary");
				List<string> AssetNames = new List<string>();

				foreach (InstrumentClass o in TradedList)
				{
					AssetNames.Add(o.Symbol);
				}
				LongData = new MLDictionary(dbTableLong, AssetNames.ToArray());
				ShortData = new MLDictionary(dbTableShort, AssetNames.ToArray());
				Print("Successfully Loaded MySQL Tables to Custom MLDictionary");

				PrintSessionClose();
			}
			#endregion
			// Methods to set up custom resources before bars are processed.

			#region Shutdown (OnTerminate)
			else if (State == State.Terminated)
			{
				if (States.HasRun)
				{
					#region Closing Formatting
					PrintTo = PrintTo.OutputTab1;
					Print ("\n");
					PrintTo = PrintTo.OutputTab2;
					Print ("\n");
					#endregion

					DoPrintAlt("##### Terminating strategy.", 1);

					#region Report Backtest Summary, Evolution and Analytics
					if (Account.Name == "Backtest")
					{
						if (Reports.BacktestSummary)
							DataTableToCSV(Reports.BacktestData, Reports.SummaryPath);

						if (Reports.EvolutionSummary)
							ExportTradeEvolution(Reports, Evolution);
					}

					DoPrint("[Stats] Date Window = " + Metrics.StartDate.ToShortDateString() + " - " + Metrics.LastDate.ToShortDateString() + " | Time Span = " + (Metrics.LastDate - Metrics.StartDate).TotalDays + " Days / " + Math.Round((Metrics.LastDate - Metrics.StartDate).TotalDays / 365, 2) + " Years", 1);
					DoPrint("[Stats] Total P&L = " + Metrics.TotalProfitLoss.ToString("C") + " / " + (Metrics.TotalProfitLoss / Metrics.InitialCapital).ToString("P") + " | CAGR = " + CalculateCAGR(Metrics).ToString("P"), 1);

					if (Account.Name == "Backtest" || Account.Name == "Sim101")
					{
						DoPrint("[Stats] Bars Not Flat = " + ((double)(TotalBars - BarsFlat) / TotalBars).ToString("P") + " | Bars Flat = " + ((double)BarsFlat / TotalBars).ToString("P"), 1);
						if (!IsBarTypeDWM())
							DoPrint("[Stats] O/N Not Flat = " + ((double)(TotalOvernights - OvernightsFlat) / TotalOvernights).ToString("P") + " | O/N Flat = " + ((double)OvernightsFlat / TotalOvernights).ToString("P"), 1);
					}

					Print ("\n");
					TradedList = TradedList.OrderByDescending(o=>o.TotalProfitLoss).ToList();
					foreach (InstrumentClass o in TradedList)
						if (o.TotalProfitLoss != 0)
							DoPrint("[Instrument P&L] " + o.Symbol + "[" + o.Index + "] = " + o.TotalProfitLoss.ToString("C") + " / " + (o.TotalProfitLoss / Metrics.TotalProfitLoss).ToString("P"), 1);
					DoPrint("[Others] Commissions = " + (-SystemPerformance.AllTrades.TradesPerformance.TotalCommission).ToString("C") + " / " + (-SystemPerformance.AllTrades.TradesPerformance.TotalCommission / Metrics.TotalProfitLoss).ToString("P"), 1);
					#endregion

					States.HasRun = false;
				}
			}
			#endregion
			// Methods to run once the strategy has been terminated. Currently displays basic analytics.

			#region Realtime Transition
			else if (State == State.Transition)
			{
				DoPrintAlt("##### Transitioning to realtime data.");
			}
			#endregion
			// Methods to run when the strategy transitions from historical to realtime data.
		}
		#endregion
		// Contains variable defaults, additional data series and indicator settings as well as setup and shutdown procedures.


	//------	Event Driven	------

		#region OnOrderUpdate
		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice, OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
		}
		#endregion

		#region OnMarketData
		protected override void OnMarketData(MarketDataEventArgs e)
		{
		}
		#endregion

		#region OnBarUpdate
		protected override void OnBarUpdate()
		{
			// Blocks calculations for multi-timeframe or instrument strategies and sets the required bars before methods are called.
			// Modify this if additional conditions (e.g. more CurrentBars or different BarsPeriodType) are required.
			if (BarsInProgress != 0 ||
				BarsPeriod.BarsPeriodType != BarsPeriodType.Minute ||
				CurrentBars[0] < 2)
				return;

			if (RotationDataChecks(TradedList, 2))
				return;

//			if (Times[0][0].Minute != 0)
//				return;

			// Runs methods at the start of day or when the first bar is evaluated.
			if ((IsFirstTickOfBar && Bars.IsFirstBarOfSession) ||
				IsBarTypeDWM() ||
				!States.StrategySetupDone)
				SessionOpen();

			// Tracks session, checks halts and filters as well as updates P&Ls.
			UpdateProfitLoss(States.HasPositions, false, Metrics, TradedList);
			States.NowTradeHalted	= CheckTradeHalts();
			States.NowFiltered		= CheckEntryFilters();
			if (IsFirstTickOfBar)
				SessionManager(SessionInfo, States);

			// Displays the status box if requested.
			if (DisplayStatusBox)
			{
				StatusString 		= GenerateStatusString(States, Metrics, TradedList);
				RenderStatusBox(StatusString);
			}

			// Independent evaluations, run on each bar.
			Evaluations();

			// Rotation methods.
			if (((IsFirstTickOfBar && BarsPeriod.BarsPeriodType == BarsPeriodType.Minute) || IsBarTypeDWM()) &&
				!States.NowTradeHalted)
			{
				if (Rotation.FirstDecision &&
					Rotation.CurrentTimeSeries >= 1)				// Modify this with the first decision conditions.
					EntryDecisions();
				else if (!Rotation.FirstDecision)
					EntryDecisions();

				if (Rotation.NextOrderTime > 0 &&
					Rotation.CurrentTimeSeries >= Rotation.NextOrderTime)
					RotationOrderCreation();

				if (Rotation.RebalanceThreshold != 0 &&
					Rotation.NextRebalanceTime > 0 &&
					Rotation.CurrentTimeSeries >= Rotation.NextRebalanceTime)
				{
					RebalanceDecision();
					RebalanceOrderCreation();
				}
			}

			if (States.HasPositions)
			{
				if (States.NowTradeHalted)
					DoFlatten("Trade Halt");
				else
					ExitDecisions();
			}

			// Runs methods at the end of day.
			if ((IsFirstTickOfBar && Times[0][0] >= ThisClose) ||
				IsBarTypeDWM())
				SessionClose();
		}
		#endregion
		// Core functionality. Updates P&L, sessions, trade halts and filters.
		// Based on that, calls the appropriate methods.
		// Related Methods:		SessionManager(SessionInfo, States)
		//						UpdateProfitLoss(HasPositions, UpdateRealized, Metrics, TradedList)
		//						GenerateStatusString(States, Metrics, TradedList)


	//------	Core Methods	------

		#region StrategySetup
		private void StrategySetup()
		{
			// FX fix for USD basis FX pairs.
			#region FX Fix (USD Basis Pairs)
			if (Instruments[0].MasterInstrument.InstrumentType == InstrumentType.Forex &&
				Instruments[0].MasterInstrument.Name.Substring(0, 3) == "USD")
			{
				Metrics.InitialCapital		= Metrics.InitialCapital * Open[0];
				Metrics.CurrentCapital		= Metrics.CurrentCapital * Open[0];
			}
			#endregion

			Metrics.StartDate = Times[0][0].Date;

			// Strategy specific calculations.
			//
			//
			//-----------
			LongSignal = new List<List<double>>();
			ShortSignal = new List<List<double>>();
			foreach (InstrumentClass o in TradedList)
			{
				long_fade_count.Add(o.Symbol, 0);
				short_fade_count.Add(o.Symbol, 0);
				long_signal_value.Add(o.Symbol, 0);
				short_signal_value.Add(o.Symbol, 0);
				LongSignal.Add(new List<double>());
				ShortSignal.Add(new List<double>());
			}

			DoPrintAlt("##### Strategy setup complete.");
			States.StrategySetupDone	= true;
		}
		#endregion
		// Contains any initial one-time calculations required. Called once bars are available before processing anything else.
		// Edit:				Strategy specific one-time calculations.

		#region SessionOpen
		private void SessionOpen()
		{
			DoPrint("*OPEN*");
			// Fix to call SessionClose on half days.
			if (!States.OnTheCloseDone &&
				Times[0][0] > ThisClose &&
				ThisClose != DateTime.MinValue)
				SessionClose();

			// Calculates session's open and close.
			ThisSession.GetNextSession(Times[0][0], true);
   			ThisOpen				= ThisSession.ActualSessionBegin;
			ThisClose				= ThisSession.ActualSessionEnd;
			States.OnTheCloseDone	= false;
			PrintSessionOpen(ThisOpen, Rotation.CurrentTimeSeries);

			// Calls the setup routine for one-time calculations.
			if (!States.StrategySetupDone)
				StrategySetup();

			// Sets new day's capital based on P&L then calculates trade sizes.
			CapitalManagement(true, Metrics);
			PositionSizerRotation(Metrics.CurrentCapital, Metrics.LeverageFactor, States, Rotation, ref TradedList, ref TargetLongList, ref TargetShortList);

			// Strategy specific calculations.
			//
			//
			//-----------
		}
		#endregion
		// Contains calculations required at the open as well as capital management and sizing methods.
		// For rotation strategies, the position sizer method is called again before any orders are created, so it might not be necessary calling it here again.
		// Edit:				Strategy specific calculations at the open.
		// Related Methods: 	CapitalManagement(ShowOutput, Metrics)
		//						PositionSizerRotation(CurrentCapital, LeverageFactor, States, Rotation, TradedList, TargetLongList, TargetShortList)

		#region SessionClose
		private void SessionClose()
		{
			DoPrint("*CLOSE*" + " / " + ThisClose.ToString());
			States.OnTheCloseDone	= true;

			// Strategy specific calculations.
			//
			//
			//-----------

			// Performs end of day reporting.
			if (Reports.MailNotifications &&
				State != State.Historical)
				StatusString = GenerateStatusString(States, Metrics, TradedList);

			DailyReporting(ThisClose, States.HasPositions, true, StatusString, Reports, Metrics, TradedList);

			DoPrint("# List: CurrentLongList (" + CurrentLongList.Count + ")");
			PrintList(CurrentLongList, 2);
			DoPrint("# List: CurrentShortList (" + CurrentShortList.Count + ")");
			PrintList(CurrentShortList, 2);

			PrintSessionClose();

			// Increment time series count for rotation models.
			Rotation.CurrentTimeSeries++;
		}
		#endregion
		// Contains calculations required at the close and daily reporting methods which mails a daily summary.
		// Edit:				Strategy specific calculations at the close.
		// Related Methods: 	DailyReporting(HasPositions, StatusString, Reports, Metrics, TradedList)
		//						GenerateStatusString(States, Metrics, TradedList)
		//						DoMail()


	//------	Heuristics / Decision Making		------

		#region Evaluations
		private void Evaluations()
		{
			// Strategy specific calculations.
			//
			//
			//-----------

			// Captures custom metrics like long/short bar and overnight exposures for the primary instrument (backtesting only).
			// Edit for additional instruments.
			#region Backtest Exposure Analytics
			if (Account.Name == "Backtest")
			{
				// For overnights.
				if (Bars.IsFirstBarOfSession)
				{
					TotalOvernights++;

					if (!States.HasPositions)
						OvernightsFlat++;
				}

				// For all bars.
				TotalBars++;

				if (!States.HasPositions)
					BarsFlat++;
			}
			#endregion

			// Captures trade evolution analytics if requested (backtesting only).
			// The framework captures results for trades in the primary instrument only, and classifies as long / short / all (doesn't capture by signal unless custom logic is implemented).
			// Edit for additional signals.
			#region Backtest Trade Evolution Analytics
			if (Account.Name == "Backtest" && Reports.EvolutionSummary && States.HasPositions)
			{
				foreach (InstrumentClass o in TradedList)
					if (o.HasPosition)
						LogTradeEvolution(o.Evolution, o.Index);
			}
			#endregion

			Metrics.LastDate = Times[0][0].Date;
		}
		#endregion
		// Contains independent calculations called on every update, regardless of sessions or positions. Also contains backtest exposure analytics.
		// Edit:				Strategy specific calcultions on each update.
		//						Tracking an alternative instrument for the backtest exposure analytics.

		#region UpdateScores
		private void UpdateScores()
		{
			double equal_weight = (double) 1/NumInstruments;

			foreach (InstrumentClass o in TradedList)
			{
				//Calculations only if current bar is "active"
				if(Times[o.Index][0] == Times[0][0])
				{
					if(OrderType == 0)
					{
						// Query both long and short signal
						long_signal_value[o.Symbol] = LongData.GetData(o.Symbol, Times[o.Index][0]);
						short_signal_value[o.Symbol] = ShortData.GetData(o.Symbol, Times[o.Index][0]);
					} else if(OrderType == 1){
						// Query long signal only
						long_signal_value[o.Symbol] = LongData.GetData(o.Symbol, Times[o.Index][0]);
						short_signal_value[o.Symbol] = 0;
					}else if(OrderType == 2){
						// Query short signal only
						long_signal_value[o.Symbol] = 0;
						short_signal_value[o.Symbol] = ShortData.GetData(o.Symbol, Times[o.Index][0]);
					}

					LongSignal[o.Index-1].Insert(0, long_signal_value[o.Symbol]);
					ShortSignal[o.Index-1].Insert(0, short_signal_value[o.Symbol]);

					long_fade_count[o.Symbol] = long_fade_count[o.Symbol] - 1;
					short_fade_count[o.Symbol] = short_fade_count[o.Symbol] - 1;

					// Possible Transactions
					if(ShortSignal[o.Index-1].Count > SignalLag &&
						LongSignal[o.Index-1].Count > SignalLag)
					{
						if(LongSignal[o.Index-1][SignalLag] >= BuySignalThreshold)
						{
							long_fade_count[o.Symbol] = ConsecutiveSignalBars;
						}

						if(ShortSignal[o.Index-1][SignalLag] >= SellSignalThreshold)
						{
							short_fade_count[o.Symbol] = ConsecutiveSignalBars;
						}

						if(long_fade_count[o.Symbol] > 0 && short_fade_count[o.Symbol] > 0)
						{
							if(o.CurrentPosition != 0)
							{
								o.Proportion = 0;
								o.Score = o.Proportion;
							}
						}else if(long_fade_count[o.Symbol] > 0 && short_fade_count[o.Symbol] <= 0){
							if(o.CurrentPosition == 0)
							{
								o.Proportion = equal_weight;
								o.Score = o.Proportion;
							}
						}else if(short_fade_count[o.Symbol] > 0 && long_fade_count[o.Symbol] <= 0){
							if(o.CurrentPosition == 0)
							{
								o.Proportion = -1*equal_weight;
								o.Score = o.Proportion;
							}
						}else if(short_fade_count[o.Symbol] <= 0 && long_fade_count[o.Symbol] <= 0){
							if(o.CurrentPosition != 0)
							{
								o.Proportion = 0;
								o.Score = o.Proportion;
							}
						}

						// Debug Signal
//						DoPrint(o.Symbol);
//						DoPrint(LongSignal[o.Index-1][0]);
//						DoPrint(LongSignal[o.Index-1][1]);
					}


//					// Debug
//					DoPrint("SYMBOL: " + o.Symbol + "-- cp:" + o.CurrentPosition);
//					DoPrint("Times: " + Times[0][0].ToLongDateString());
//					DoPrint("Times: " + Times[o.Index][0] + " ====  " + Times[0][0]);
//					DoPrint("After ============== Long Signal:" + long_signal_value[o.Symbol] + "=== Short Signal:" + short_signal_value[o.Symbol]);
//					DoPrint("After ============== Long Fade:" + long_fade_count[o.Symbol] + "=== Short Fade:" + short_fade_count[o.Symbol]);
//					DoPrint("Symbol: " + o.Symbol + "-- Prop:" + o.Proportion + "-- score:" + o.Score);
//					DoPrint("++++++++++++++++++++++++++++++++++++++");
//					DoPrint("=====================================");
//					DoPrint("++++++++++++++++++++++++++++++++++++++");
				}

			}




			if (Rotation.RotationInverseMode)
				SortListByScore(ref TradedList, true);
			else
				SortListByScore(ref TradedList, false);
		}
		#endregion
		// Perform scoring to create RotationList then sort accordingly.

		#region LongFilter
		private bool LongFilter(InstrumentClass o)
		{
			string MiscInfo;

			// If cutoff threshold mode is used.
			if (Rotation.RotationCutoffMode &&
				((!Rotation.RotationInverseMode && o.Score <= Rotation.CutoffLongThreshold) || (Rotation.RotationInverseMode && o.Score >= Rotation.CutoffLongThreshold)))
			{
				Rotation.LongCutoffHit	= true;
				return true;
//				MiscInfo = "Long Cutoff Threshold Reached...";
//				DoPrint("Cutoff (Long) > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2) + " | " + MiscInfo, ModelTag);
			}

			if (Rotation.RotationLongFilter)
			{
				// Filtering conditions, return false if allowed.
				if (o.Score > 0)
					return false;
				// Return true if instrument is filtered.
				else
				{
					MiscInfo = "Non Positive Score";
					DoPrint("Filtering Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2) + " | " + MiscInfo);
					return true;
				}
			}
			// Return false if filter is not used.
			else
				return false;
		}
		#endregion
		// Put in the long filtering heuristics here and call this function when filtering is required.
		// Returns true if it fails the trading conditions, otherwise returns false.

		#region ShortFilter
		private bool ShortFilter(InstrumentClass o)
		{
			string MiscInfo;

			if (Rotation.RotationCutoffMode &&
				((!Rotation.RotationInverseMode && o.Score >= Rotation.CutoffShortThreshold) || (Rotation.RotationInverseMode && o.Score <= Rotation.CutoffShortThreshold)))
			{
				Rotation.ShortCutoffHit	= true;
				return true;
//				MiscInfo = "Short Cutoff Threshold Reached...";
//				DoPrint("Cutoff (Short) > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2) + " | " + MiscInfo, ModelTag);
			}

			if (Rotation.RotationShortFilter)
			{
				// Filtering conditions, return false if allowed.
				if (Close[0] < 0)
					return false;
				// Return true if instrument is filtered.
				else
				{
					MiscInfo = "Positive Score";
					DoPrint("Filtering Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2) + " | " + MiscInfo);
					return true;
				}
			}
			// Return false if filter is not used.
			else
				return false;
		}
		#endregion
		// Put in the short filtering heuristics here and call this function when filtering is required.
		// Returns true if it fails the trading conditions, otherwise returns false.

		#region EntryDecisions
		private void EntryDecisions()
		{
			// Strategy specific calculations.
			//
			//
			//-----------

			RotationDecision();
		}
		#endregion
		// Only accessed if NowInSession, NowEntryAllowed, !NowFiltered, !NowTradeHalted.
		// Edit:				Strategy specific entry signals.

		#region ExitDecisions
		private void ExitDecisions()
		{
			// Checks positions based on time stops and stop losses if either are selected.
			#region Generic Exit Conditions
			foreach (InstrumentClass o in TradedList)
			{
				if (o.HasPosition)
				{
					// Checks time stops.
					if (!o.PendingExit &&
						IsFirstTickOfBar &&
						TimeStopBars > 0 &&
						BarsSinceEntryExecution(o.Index, "", 0) >= TimeStopBars - 1)
					{
						if (o.CurrentPosition > 0)
						{
							ExitLong(o.Index, 0, "ExitTimeStop", "");

							DecisionInfo		= "# Signal: [Exit] Short " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]) + " | Time Stop Bars = " + TimeStopBars;
							GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
							o.PendingExit 		= true;
						}
						else
						{
							ExitShort(o.Index, 0, "ExitTimeStop", "");

							DecisionInfo		= "# Signal: [Exit] Long " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]) + " | Time Stop Bars = " + TimeStopBars;
							GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
							o.PendingExit 		= true;
						}
					}
					// Checks stop losses.
					if (!o.PendingExit &&
						o.StopPrice != 0)
					{
						if (o.CurrentPosition > 0 &&
							Closes[o.Index][0] <= o.StopPrice)
						{
							ExitLong(o.Index, 0, "ExitStopLoss", "");

							DecisionInfo		= "# Signal: [Exit] Short " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]) + " | Stop Loss Hit = " + o.StopPrice;
							GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
							o.PendingExit 		= true;
						}
						else if (o.CurrentPosition < 0 &&
								 Closes[o.Index][0] >= o.StopPrice)
						{
							ExitShort(o.Index, 0, "ExitStopLoss", "");

							DecisionInfo		= "# Signal: [Exit] Long " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]) + " | Stop Loss Hit = " + o.StopPrice;
							GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
							o.PendingExit 		= true;
						}
					}
					// Checks target prices.
					if (!o.PendingExit &&
						o.TargetPrice != 0)
					{
						if (o.CurrentPosition > 0 &&
							Closes[o.Index][0] >= o.TargetPrice)
						{
							ExitLong(o.Index, 0, "ExitTargetProfit", "");

							DecisionInfo		= "# Signal: [Exit] Short " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]) + " | Target Price Hit = " + o.TargetPrice;
							GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
							o.PendingExit 		= true;
						}
						else if (o.CurrentPosition < 0 &&
								 Closes[o.Index][0] <= o.TargetPrice)
						{
							ExitShort(o.Index, 0, "ExitTargetProfit", "");

							DecisionInfo		= "# Signal: [Exit] Long " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]) + " | Target Price Hit = " + o.TargetPrice;
							GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
							o.PendingExit 		= true;
						}
					}
					// Checks trail stops.
					if (!o.PendingExit &&
						o.TrailStopPrice != 0)
					{
						if (o.CurrentPosition > 0 &&
							Closes[o.Index][0] <= o.TrailStopPrice)
						{
							ExitLong(o.Index, 0, "ExitTrailStop", "");

							DecisionInfo		= "# Signal: [Exit] Short " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]) + " | Trail Stop Hit = " + o.TrailStopPrice;
							GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
							o.PendingExit 		= true;
						}
						else if (o.CurrentPosition < 0 &&
								 Closes[o.Index][0] >= o.TrailStopPrice)
						{
							ExitShort(o.Index, 0, "ExitTrailStop", "");

							DecisionInfo		= "# Signal: [Exit] Long " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]) + " | Trail Stop Hit = " + o.TrailStopPrice;
							GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
							o.PendingExit 		= true;
						}
					}
				}
			}
			#endregion

			// Resets the PendingExit flag for each instrument.
			#region Reset Pending Exits
			foreach (InstrumentClass o in TradedList)
				o.PendingExit = false;
			#endregion
		}
		#endregion
		// Only accessed if one or more traded instruments has a position.
		// Edit:				Strategy specific exit signals.

		#region OnExecutionUpdate
		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity, MarketPosition marketPosition, string orderId, DateTime time)
		{
			// Sets position, quantity and price variables if a new position is taken or clears them if an existing position is closed.
			States.HasPositions	=	CheckPositions(TradedList);

			// Updates P&L variables when orders are filled, then runs required reporting methods. The generic stop loss is also calculated here.
			// Ensure that all exit order strings begin with "Exit" for logic to work.
			#region Filled Order Logic
			if (execution.Order.OrderState == OrderState.Filled &&
				LastOrderId != orderId)
			{
				LastOrderId = orderId;

				// Calculates slippage metrics.
				string ExecSubject;
				string ExecType;
				string ExecSymbol				= Instrument.MasterInstrument.Name;
				bool UpdateRealized				= false;
				int Signal						= 0;
				int TradedListIndex				= TradedList.FindIndex(o=>o.Index == BarsInProgress);
				int Rounding					= 3;
				int Quantity					= execution.Order.Quantity;
				double AveragePrice				= execution.Order.AverageFillPrice;
				double Slippage					= (execution.MarketPosition == MarketPosition.Long ? (AveragePrice - TradedList[TradedListIndex].DecisionPrice) : -(AveragePrice - TradedList[TradedListIndex].DecisionPrice));
				double SlippagePct				= Slippage / TradedList[TradedListIndex].DecisionPrice;
				double Notional					= (Instruments[BarsInProgress].MasterInstrument.InstrumentType != InstrumentType.Future ? (execution.MarketPosition == MarketPosition.Long ? Quantity * AveragePrice : -Quantity * AveragePrice) : (execution.MarketPosition == MarketPosition.Long ? Quantity * AveragePrice * Instruments[BarsInProgress].MasterInstrument.PointValue : -Quantity * AveragePrice * Instruments[BarsInProgress].MasterInstrument.PointValue));

				// Edit the if condition here if necessary to accommodate other exit signal strings.
				if (execution.Order.Name.ToLower().Contains("exit") || execution.Order.Name == "Sell" || execution.Order.Name == "Buy to cover" || execution.Order.Name == "Profit target" || execution.Order.Name == "Stop loss" || execution.Order.Name == "Close position")
				{
					DoPrintAlt("# Execution: [Exit] " + execution.Order.OrderType + " " + execution.MarketPosition + " " + Instrument.MasterInstrument.Name + " = " + Quantity + " @ " + Math.Round(AveragePrice, Rounding) + " | Notional = " + Notional.ToString("C"));
					ExecSubject 	= "Exit";
					UpdateRealized	= true;
					Signal			= (execution.MarketPosition == MarketPosition.Long ? 2 : 1);

					// Manage the aggregation of trade evolution data into the corresponding aggregate data structures. Edit here for custom logic and signals.
					#region Trade Evolution
					if (Account.Name == "Backtest" && Reports.EvolutionSummary &&
						Positions[BarsInProgress].MarketPosition == MarketPosition.Flat)
					{
						MergeTradeEvolution(Evolution[0], TradedList[TradedListIndex].Evolution);

						// If we just closed a long.
						if (execution.MarketPosition == MarketPosition.Short)
						{
							MergeTradeEvolution(Evolution[1], TradedList[TradedListIndex].Evolution);

							if (TradedList[TradedListIndex].Evolution.Average.Length > 0)
							{
								if (TradedList[TradedListIndex].Evolution.Average[TradedList[TradedListIndex].Evolution.Average.Length - 1] >= 0)
								{
									MergeTradeEvolution(Evolution[3], TradedList[TradedListIndex].Evolution);
									MergeTradeEvolution(Evolution[5], TradedList[TradedListIndex].Evolution);
								}
								else
								{
									MergeTradeEvolution(Evolution[4], TradedList[TradedListIndex].Evolution);
									MergeTradeEvolution(Evolution[6], TradedList[TradedListIndex].Evolution);
								}
							}
						}
						// Otherwise it was a short.
						else
						{
							MergeTradeEvolution(Evolution[2], TradedList[TradedListIndex].Evolution);

							if (TradedList[TradedListIndex].Evolution.Average.Length > 0)
							{
								if (TradedList[TradedListIndex].Evolution.Average[TradedList[TradedListIndex].Evolution.Average.Length - 1] >= 0)
								{
									MergeTradeEvolution(Evolution[3], TradedList[TradedListIndex].Evolution);
									MergeTradeEvolution(Evolution[7], TradedList[TradedListIndex].Evolution);
								}
								else
								{
									MergeTradeEvolution(Evolution[4], TradedList[TradedListIndex].Evolution);
									MergeTradeEvolution(Evolution[8], TradedList[TradedListIndex].Evolution);
								}
							}
						}

						// Erase the current trade data for future use.
						ClearTradeEvolution(TradedList[TradedListIndex].Evolution);
					}
					#endregion
				}
				else if (execution.Order.Name.ToLower().Contains("reduce"))
				{
					DoPrintAlt("# Execution: [Exit / Partial] " + execution.Order.OrderType + " " + execution.MarketPosition + " " + Instrument.MasterInstrument.Name + " = " + Quantity + " @ " + Math.Round(AveragePrice, Rounding) + " | Notional = " + Notional.ToString("C"));
					ExecSubject 	= "Partial Exit";
					UpdateRealized	= true;
					Signal			= (execution.MarketPosition == MarketPosition.Long ? 2 : 1);
				}
				else
				{
					DoPrintAlt("# Execution: [Entry] " + execution.Order.OrderType + " " + execution.MarketPosition + " " + Instrument.MasterInstrument.Name + " = " + Quantity + " @ " + Math.Round(AveragePrice, Rounding) + " | Notional = " + Notional.ToString("C"));
					ExecSubject = "Entry";

					// Calculates the initial stop/trail/target prices if they are used.
					if (StopLossPct > 0)
					{
						TradedList[TradedListIndex].StopPrice		= (TradedList[TradedListIndex].CurrentPosition > 0) ? Instrument.MasterInstrument.RoundToTickSize(TradedList[TradedListIndex].AveragePrice * (100 - StopLossPct) / 100) : Instrument.MasterInstrument.RoundToTickSize(TradedList[TradedListIndex].AveragePrice * (100 + StopLossPct) / 100);
						DoPrint("[Stop] Stop Price Set = "  + TradedList[TradedListIndex].StopPrice);
					}
					if (TargetProfitPct > 0)
					{
						TradedList[TradedListIndex].TargetPrice		= (TradedList[TradedListIndex].CurrentPosition > 0) ? Instrument.MasterInstrument.RoundToTickSize(TradedList[TradedListIndex].AveragePrice * (100 + TargetProfitPct) / 100) : Instrument.MasterInstrument.RoundToTickSize(TradedList[TradedListIndex].AveragePrice * (100 - TargetProfitPct) / 100);
						DoPrint("[Target] Target Price Set = "  + TradedList[TradedListIndex].TargetPrice);
					}
					if (TrailStopPct > 0)
					{
						TradedList[TradedListIndex].TrailStopPrice	= (TradedList[TradedListIndex].CurrentPosition > 0) ? Instrument.MasterInstrument.RoundToTickSize(TradedList[TradedListIndex].AveragePrice * (100 - TrailStopPct) / 100) : Instrument.MasterInstrument.RoundToTickSize(TradedList[TradedListIndex].AveragePrice * (100 + TrailStopPct) / 100);
						DoPrint("[Trail] Trail Stop Set = "  + TradedList[TradedListIndex].TrailStopPrice);
					}
				}

				if (execution.MarketPosition == MarketPosition.Long)
				{
					// We either rebalanced, initiated a new long, or we exited a short.
					if (RebalIncLongList.Any(o => o.Symbol == ExecSymbol))
					{
						ExecType	= "RebalInc";
						RebalIncLongList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
					else if (RebalRedShortList.Any(o => o.Symbol == ExecSymbol))
					{
						ExecType	= "RebalRed";
						RebalRedShortList.RemoveAll(o=>o.Symbol == ExecSymbol);

						if (TradedList[TradedListIndex].CurrentPosition == 0)
							CurrentShortList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
					else if (ExitShortList.Any(o => o.Symbol == ExecSymbol) &&
							 CurrentShortList.Any(o => o.CurrentPosition == execution.Order.Quantity))
					{
						ExecType	= "Exit";
						CurrentShortList.RemoveAll(o=>o.Symbol == ExecSymbol);
						ExitShortList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
					else if (EnterLongList.Any(o => o.Symbol == ExecSymbol))
					{
						ExecType	= "Entry";
						CurrentLongList.Add(EnterLongList.Find(o=>o.Symbol == ExecSymbol));
						EnterLongList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
					else
					{
						ExecType	= "Stop";
						CurrentShortList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
				}
				else
				{
					// We either rebalanced, initiated a new short, or we exited a long.
					if (RebalIncShortList.Any(o => o.Symbol == ExecSymbol))
					{
						ExecType	= "RebalInc";
						RebalIncShortList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
					else if (RebalRedLongList.Any(o => o.Symbol == ExecSymbol))
					{
						ExecType	= "RebalRed";
						RebalRedLongList.RemoveAll(o=>o.Symbol == ExecSymbol);

						if (TradedList[TradedListIndex].CurrentPosition == 0)
							CurrentLongList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
					else if (ExitLongList.Any(o => o.Symbol == ExecSymbol) &&
							 CurrentLongList.Any(o => o.CurrentPosition == execution.Order.Quantity))
					{
						ExecType	= "Exit";
						CurrentLongList.RemoveAll(o=>o.Symbol == ExecSymbol);
						ExitLongList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
					else if (EnterShortList.Any(o => o.Symbol == ExecSymbol))
					{
						ExecType	= "Entry";
						CurrentShortList.Add(EnterShortList.Find(o=>o.Symbol == ExecSymbol));
						EnterShortList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
					else
					{
						ExecType	= "Stop";
						CurrentLongList.RemoveAll(o=>o.Symbol == ExecSymbol);
					}
				}

				// Updates P&L information for the strategy and individual instruments.
				UpdateProfitLoss(Signal, AveragePrice, Instrument.MasterInstrument.Name, States.HasPositions, UpdateRealized, Metrics, TradedList);

				#region Reporting
				// If running in realtime, print execution to the trade log and send a mail notification. Then, clear decision variables.
				if (State != State.Historical)
				{
					ExportTrade(Reports,
							Time[0].ToString("d")																	+","+	// Date
							Time[0].ToString("HH:mm:ss")															+","+	// Time
							DateTime.Now																			+","+	// Local Date / Time
							Name																					+","+	// Model Prefix
							Instrument.MasterInstrument.Name														+","+	// Traded Instrument
							ExecSubject																				+","+  	// Entry / Exit
							execution.MarketPosition																+","+  	// Direction
							Quantity											         							+","+	// Quantity
							AveragePrice																			+","+  	// Average Price
							Notional																				+","+	// Notional
							SlippagePct																				+","+  	// Slippage Percent
							(Signal > 0 ? Metrics.LastTradeProfitLoss : 0)											+","+  	// P&L Currency
							(Signal > 0 ? Metrics.LastTradeProfitLossPct : 0));												// P&L Percent

					if (Reports.MailNotifications)
					{
						StatusString 	= GenerateStatusString(States, Metrics, TradedList);

						MailString 		= execution.Order.OrderType + " " + execution.MarketPosition + " " + Instrument.MasterInstrument.Name + " = " + Quantity + " @ " + Math.Round(AveragePrice, Rounding);
						MailString 		= MailString + "\n\n" + TradedList[TradedListIndex].DecisionString;
						MailString 		= MailString + "\nSlippage       : " + Math.Round(Slippage, Rounding) + " (" + SlippagePct.ToString("P") + ")"  + "\nNotional       : " + Notional.ToString("C");
						if (UpdateRealized)
							MailString	= MailString + "\n\nLast Trade     : " + Metrics.LastTradeProfitLoss.ToString("C") + " / " + Metrics.LastTradeProfitLossPct.ToString("P");
						MailString 		= MailString + "\n\n" + execution.Order.ToString() + "\n";

						DoMail(ExecSubject, MailString, StatusString);

						TradedList[TradedListIndex].DecisionPrice	= 0;
						TradedList[TradedListIndex].DecisionString 	= null;
					}
				}
				#endregion
			}
			#endregion
		}
		#endregion
		// Updates P&L and position information when orders are filled. Also includes reporting and mails execution reports.
		// Ensure that all exit signal strings begin with "Exit" for logic to work.
		// Also aggregates backtest trade evolution data.
		// Edit:				If other exit signal strings are used.
		//						Modify display rounding for other instruments (default is 3 decimals).
		//						Custom backtest trade evolution analytics.
		// Related Methods: 	CheckPositions(TradedList)
		//						UpdateProfitLoss(HasPositions, UpdateRealized, Metrics, TradedList)
		//						GenerateStatusString(States, Metrics, TradedList)
		//						ExportTrade()
		//						DoMail()
		//						MergeTradeEvolution()

		#region OnPositionUpdate
		protected override void OnPositionUpdate(Position position, double averagePrice, int quantity, MarketPosition marketPosition)
		{
			// Hedging unwind heuristics go here.
		}
		#endregion
		// Used to manage and unwind position hedges.


	//------	Rotation Methods	------

		#region RotationDecision
		private void RotationDecision()
		{
			DoPrint("-----------------------------------------------");
			DoPrintAlt("[Rotation Decision]");
			Rotation.FirstDecision = false;

			// Sets the time of the next decision, rebalance and entry (measured by relative time series) if necessary.
			if (Rotation.DecisionFrequency > 0)
				Rotation.NextDecisionTime	= Rotation.CurrentTimeSeries + Rotation.DecisionFrequency;
			Rotation.NextRebalanceTime		= Rotation.CurrentTimeSeries;
			Rotation.NextOrderTime			= Rotation.CurrentTimeSeries + Rotation.OrderDelayBars;

			// Perform scoring to create RotationList then sort accordingly.
			UpdateScores();

			// RotationList reporting.
			DoPrint("# List: RotationList (" + TradedList.Count + ")");
			PrintList(TradedList, 1);
			DoPrint("-----------------------------------------------");

			// Create the new lists of instruments we should be long and short.
			if (!Rotation.RotationCutoffMode)
			{
				if (Rotation.NumLongs > 0)
					GenerateLongList(TradedList, ref TargetLongList);
				if (Rotation.NumShorts > 0)
					GenerateShortList(TradedList, ref TargetShortList);
			}
			else
			{
				if (Rotation.RotationCutoffLongs)
					GenerateCutoffLongList(TradedList, ref TargetLongList);
				if (Rotation.RotationCutoffShorts)
					GenerateCutoffShortList(TradedList, ref TargetShortList);
			}

			// Check and resolve conflicts in both lists.
			RemoveListDuplicates(ref TargetLongList, ref TargetShortList, Reports);

			// NewList reporting.
			DoPrint("-----------------------------------------------");
			if (TargetLongList.Count > 0)
			{
				DoPrint("# List: TargetLongList (" + TargetLongList.Count + ")");
				PrintList(TargetLongList, 0);
			}
			if (TargetShortList.Count > 0)
			{
				DoPrint("# List: TargetShortList (" + TargetShortList.Count + ")");
				PrintList(TargetShortList, 0);
			}
			DoPrint("-----------------------------------------------");

			// Create the lists of instruments we need to exit and enter in order to get the desired exposure.
			ExitLongList 	= CurrentLongList.Where(c => !TargetLongList.Any(d => d.Symbol == c.Symbol)).ToList();
			ExitShortList	= CurrentShortList.Where(c => !TargetShortList.Any(d => d.Symbol == c.Symbol)).ToList();
			EnterLongList 	= TargetLongList.Where(c => !CurrentLongList.Any(d => d.Symbol == c.Symbol)).ToList();
			EnterShortList	= TargetShortList.Where(c => !CurrentShortList.Any(d => d.Symbol == c.Symbol)).ToList();

			// ExitList and GoList reporting.
			if (ExitLongList.Count > 0)
			{
				DoPrint("# List: ExitLongList (" + ExitLongList.Count + ")");
				PrintList(ExitLongList, 0);
			}
			if (ExitShortList.Count > 0)
			{
				DoPrint("# List: ExitShortList (" + ExitShortList.Count + ")");
				PrintList(ExitShortList, 0);
			}
			if (EnterLongList.Count > 0)
			{
				DoPrint("# List: EnterLongList (" + EnterLongList.Count + ")");
				PrintList(EnterLongList, 0);
			}
			if (EnterShortList.Count > 0)
			{
				DoPrint("# List: EnterShortList (" + EnterShortList.Count + ")");
				PrintList(EnterShortList, 0);
			}
			if (ExitLongList.Count + ExitShortList.Count + EnterLongList.Count + EnterShortList.Count == 0)
			{
				DoPrint("[Rotation] No changes to positions.");
				Rotation.NextOrderTime	= 0;
			}

			Rotation.FirstDecision			= false;
			DoPrint("-----------------------------------------------");
		}
		#endregion

		#region RotationOrderCreation
		private void RotationOrderCreation()
		{
			DoPrint("[Creating Rotation Orders]");
			Rotation.NextOrderTime	= 0;

			// Calculate desired position sizes.
			PositionSizerRotation(Metrics.CurrentCapital, Metrics.LeverageFactor, States, Rotation, ref TradedList, ref TargetLongList, ref TargetShortList);
			PrintList(TradedList, 3);

			// First, exit the positions we need to exit.
			foreach (InstrumentClass o in ExitLongList)
			{
				ExitLong(o.Index, o.CurrentPosition, "ExitRotationLong" + o.Symbol, "");

				DecisionInfo		= "# Signal: [Exit] Short " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]);
				GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
			}

			foreach (InstrumentClass o in ExitShortList)
			{
				ExitShort(o.Index, -o.CurrentPosition, "ExitRotationShort" + o.Symbol, "");

				DecisionInfo		= "# Signal: [Exit] Long " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]);
				GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
			}

			// Then we initiate new positions.
			foreach (InstrumentClass o in EnterLongList)
			{
				EnterLong(o.Index, o.DesiredPosition, "RotationLong" + o.Symbol);

				DecisionInfo		= "# Signal: [Entry] Long " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]);
				GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
			}

			foreach (InstrumentClass o in EnterShortList)
			{
				EnterShort(o.Index, -o.DesiredPosition, "RotationShort" + o.Symbol);

				DecisionInfo		= "# Signal: [Entry] Short " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]);
				GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
			}

			DoPrint("-----------------------------------------------");
		}
		#endregion
		// Sends orders required to move from CurrentLongList and CurrentShortList to TargetLongList and TargetShortList.
		// Position size method is called again here.
		// Related Methods: 	PositionSizerRotation(CurrentCapital, LeverageFactor, States, Rotation, TradedList, TargetLongList, TargetShortList)

		#region RebalanceDecision
		private void RebalanceDecision()
		{
			int RebalanceShares;
			double RebalanceDifference;

			DoPrint("[Rebalance Decision]");
			Rotation.NextRebalanceTime	= 0;

			// Sets the time of the next rebalance (measured by relative time series) if necessary.
			if (Rotation.RebalanceFrequency > 0)
				Rotation.NextRebalanceTime	= Rotation.CurrentTimeSeries + Rotation.RebalanceFrequency;

			// Calculated desired position sizes.
			PositionSizerRotation(Metrics.CurrentCapital, Metrics.LeverageFactor, States, Rotation, ref TradedList, ref TargetLongList, ref TargetShortList);
			//PrintList(TradedList, 3);

			// Check each position we are currently long, which we are not waiting to exit.
			foreach (InstrumentClass o in CurrentLongList)
			{
				if (!ExitLongList.Any(p => p.Symbol == o.Symbol))
				{
					RebalanceShares		= o.DesiredPosition - o.CurrentPosition;
					RebalanceDifference = 1.0 * RebalanceShares / o.CurrentPosition;
					//Print (o.Symbol + " // " + RebalanceDifference + " // Desired=" + o.DesiredPosition + " // Current=" + o.CurrentPosition);

					// If we need to buy to increase our long position.
					if (RebalanceDifference > RebalanceThreshold / 100)
					{
						//Print("Desired = " + o.DesiredPosition + " // Current = " + o.CurrentPosition);
						DoPrint("Increasing Long > " + o.Symbol + "[" + o.Index + "] = " + RebalanceShares + " / " + RebalanceDifference.ToString("P"));
						RebalIncLongList.Add(o);
						//RebalIncLongList.Find(p=>p.Symbol == o.Symbol).DesiredPosition 	= Math.Abs(RebalanceShares);
						//Print("+ve " + RebalanceDifference + " // " + RebalanceThreshold/100);

					}
					// If we need to sell to reduce our long position.
					else if (RebalanceDifference < -RebalanceThreshold / 100)
					{
						//Print("Desired = " + o.DesiredPosition + " // Current = " + o.CurrentPosition);
						DoPrint("Reducing Long > " + o.Symbol + "[" + o.Index + "] = " + RebalanceShares + " / " + RebalanceDifference.ToString("P"));
						RebalRedLongList.Add(o);
						//RebalRedLongList.Find(p=>p.Symbol == o.Symbol).DesiredPosition 	= Math.Abs(RebalanceShares);
						//Print("-ve " + RebalanceDifference + " // " + RebalanceThreshold/100);

					}
				}
			}

			// Check each position we are currently short.
			foreach (InstrumentClass o in CurrentShortList)
			{
				if (!ExitShortList.Any(p => p.Symbol == o.Symbol))
				{
					RebalanceShares		= o.DesiredPosition - o.CurrentPosition;
					RebalanceDifference = 1.0 * RebalanceShares / o.CurrentPosition;
					//Print (o.Symbol + " // " + RebalanceDifference + " // Desired=" + o.DesiredPosition + " // Current=" + o.CurrentPosition);

					// If we need to sell to increase our short position.
					if (RebalanceDifference > RebalanceThreshold / 100)
					{
						//Print("Desired = " + o.DesiredPosition + " // Current = " + o.CurrentPosition);
						DoPrint("Increasing Short > " + o.Symbol + "[" + o.Index + "] = " + RebalanceShares + " / " + RebalanceDifference.ToString("P"));
						RebalIncShortList.Add(o);
						//RebalIncShortList.Find(p=>p.Symbol == o.Symbol).DesiredPosition 	= Math.Abs(RebalanceShares);
						//Print("+ve " + RebalanceDifference + " // " + RebalanceThreshold/100);

					}
					// If we need to buy to reduce our short position.
					else if (RebalanceDifference < -RebalanceThreshold / 100)
					{
						//Print("Desired = " + o.DesiredPosition + " // Current = " + o.CurrentPosition);
						DoPrint("Reducing Short > " + o.Symbol + "[" + o.Index + "] = " + RebalanceShares + " / " + RebalanceDifference.ToString("P"));
						RebalRedShortList.Add(o);
						//RebalRedShortList.Find(p=>p.Symbol == o.Symbol).DesiredPosition 	= Math.Abs(RebalanceShares);
						//Print("-ve " + RebalanceDifference + " // " + RebalanceThreshold/100);

					}
				}
			}

			// RebalanceList reporting.
			if (RebalIncLongList.Count > 0)
			{
				DoPrint("# List: RebalIncLongList (" + RebalIncLongList.Count + ")");
				PrintList(RebalIncLongList, 7);
			}
			if (RebalRedLongList.Count > 0)
			{
				DoPrint("# List: RebalRedLongList (" + RebalRedLongList.Count + ")");
				PrintList(RebalRedLongList, 7);
			}
			if (RebalIncShortList.Count > 0)
			{
				DoPrint("# List: RebalIncShortList (" + RebalIncShortList.Count + ")");
				PrintList(RebalIncShortList, 7);
			}
			if (RebalRedShortList.Count > 0)
			{
				DoPrint("# List: RebalRedShortList (" + RebalRedShortList.Count + ")");
				PrintList(RebalRedShortList, 7);
			}
			if (RebalIncLongList.Count + RebalRedLongList.Count + RebalIncShortList.Count + RebalRedShortList.Count == 0)
				DoPrint("[Rebalance] No rebalancing required.");

			DoPrint("-----------------------------------------------");
		}
		#endregion
		// Position size method is called again here.
		// Related Methods: 	PositionSizerRotation(CurrentCapital, LeverageFactor, States, Rotation, TradedList, TargetLongList, TargetShortList)

		#region RebalanceOrderCreation
		private void RebalanceOrderCreation()
		{
			if (RebalIncLongList.Count + RebalRedLongList.Count + RebalIncShortList.Count + RebalRedShortList.Count == 0)
				return;

			DoPrint("[Creating Rebalance Orders]");

			foreach (InstrumentClass o in RebalIncLongList)
			{
				EnterLong(o.Index, o.DesiredPosition - o.CurrentPosition, "RebalLong" + o.Symbol + Metrics.RebalCounter);

				DecisionInfo					= "# Signal: [Entry / Increased] Long " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]);
				GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
				Metrics.RebalCounter++;
			}

			foreach (InstrumentClass o in RebalIncShortList)
			{
				EnterShort(o.Index, o.CurrentPosition - o.DesiredPosition, "RebalShort" + o.Symbol + Metrics.RebalCounter);

				DecisionInfo					= "# Signal: [Entry / Increased] Short " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]);
				GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
				Metrics.RebalCounter++;
			}

			foreach (InstrumentClass o in RebalRedLongList)
			{
				ExitLong(o.Index, o.CurrentPosition - o.DesiredPosition, "ReduceLong" + o.Symbol, "");

				DecisionInfo					= "# Signal: [Exit / Partial] Short " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]);
				GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
			}

			foreach (InstrumentClass o in RebalRedShortList)
			{
				ExitShort(o.Index, o.DesiredPosition - o.CurrentPosition, "ReduceShort" + o.Symbol, "");

				DecisionInfo					= "# Signal: [Exit / Partial] Long " + o.Symbol + " = " + Instruments[o.Index].MasterInstrument.RoundToTickSize(Closes[o.Index][0]);
				GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);
			}

			DoPrint("-----------------------------------------------");
		}
		#endregion
		// Sends orders required to achieve desired position sizes when out of range.

		#region GenerateLongList
		private void GenerateLongList(List<InstrumentClass> SourceList, ref List<InstrumentClass> NewList)
		{
			#region Reporting/Housekeeping
			if (!Rotation.RotationLongFilter)
				DoPrint("[Rotation] Generating New Long List (Unfiltered)");
			else
				DoPrint("[Rotation] Generating New Long List (Filtered)");

			if (Rotation.RotationInverseMode)
				DoPrint("[Rotation] Inverse Mode Activated, Buying Lowest Scores");
			if (Rotation.SkipTopLongs > 0)
				DoPrint("[Rotation] Skipping Top Longs | Skipped = " + Rotation.SkipTopLongs);

			// Clear the previous list.
			NewList.Clear();
			#endregion

			// Sort the source list.
			#region SourceList Sorting
			// If inverse mode is set to 1, we sort from lowest to highest and buy those with low scores.
			if (!Rotation.RotationInverseMode)
				SortListByScore(ref SourceList, false);
			else
				SortListByScore(ref SourceList, true);
			#endregion

			// Form the new list.
			#region NewList Creation
			foreach (InstrumentClass o in SourceList)
			{
				if (SourceList.IndexOf(o) <= Rotation.SkipTopLongs - 1)
					DoPrint ("Skipping Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
				else if (!LongFilter(o))
				{
					NewList.Add(o);
					DoPrint ("Adding Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
				}

				// Insert break conditions here.
				// Stop when we have gotten the number of items we wanted.
				if (NewList.Count >= Rotation.NumLongs)
				{
					DoPrint("[Rotation] Full Long List Created Successfully | Instruments = " + NewList.Count + " / " + Rotation.NumLongs);
					break;
				}
				// If we have shorts, we don't progress further than halfway down the list.
				else if (Rotation.RotationShortFilter &&
						 Rotation.NumShorts > 0 &&
					 	 SourceList.IndexOf(o) == Math.Floor(Rotation.NumInstruments / 2.0) - 1)
				{
					DoPrint("[Rotation] Reached Halfway Point | Instruments = " + NewList.Count + " / " + Rotation.NumLongs);
					break;
				}
			}
			#endregion

			// Check FilterMode and act, if insufficient instruments are added to the list.
			#region FilterMode Pass
			// If set to 2, bypass the filter and accept highest/lowest scorers, regardless of whether or not they pass the filter to maintain size.
			if (Rotation.FilterMode == 2 &&
				NewList.Count < Rotation.NumLongs)
			{
				DoPrint("[Rotation] Maintaining Desired Size w/ Bypasses");

				foreach (InstrumentClass o in SourceList)
				{
					if (NewList.Any(p => p.Symbol == o.Symbol))
						DoPrint("Existing Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					else
					{
						NewList.Add(o);
						DoPrint("Adding Bypassed Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					}

					// Insert break conditions here.
					// If we have gotten the number of items we wanted.
					if (NewList.Count >= Rotation.NumLongs)
					{
						DoPrint("[Rotation] Full Long List Created Successfully w/ Bypasses | Instruments = " + NewList.Count + " / " + Rotation.NumLongs);
						break;
					}
					// If we have shorts, we don't progress further than halfway down the list.
					else if (Rotation.RotationShortFilter &&
							 Rotation.NumShorts > 0 &&
							 SourceList.IndexOf(o) == Math.Floor(Rotation.NumInstruments / 2.0) - 1)
					{
						DoPrint("[Rotation] Reached Halfway Point, Accepting Fewer Instruments | Instruments = " + NewList.Count + " / " + Rotation.NumLongs);
						break;
					}
				}
			}
			// If set to 1, do nothing unless we have insufficient instruments in the list, in which case bypass the filter till we have FilterMinSize instruments.
			else if (Rotation.FilterMode == 1 &&
					 NewList.Count < Rotation.FilterMinSize)
			{
				DoPrint("[Rotation] Reaching Minimum Size w/ Bypasses | Minimum Size = " + Rotation.FilterMinSize);

				foreach (InstrumentClass o in SourceList)
				{
					if (NewList.Any(p => p.Symbol == o.Symbol))
						DoPrint("Existing Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					else
					{
						NewList.Add(o);
						DoPrint("Adding Bypassed Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					}

					// Insert break conditions here.
					// Stop when we have gotten the number of items we wanted.
					if (NewList.Count >= Rotation.FilterMinSize)
					{
						DoPrint("[Rotation] Minimum Size Long List Created | Instruments = " + NewList.Count + " / " + Rotation.FilterMinSize);
						break;
					}
					// If we have shorts, we don't progress further than halfway down the list.
					else if (Rotation.RotationShortFilter &&
							 Rotation.NumShorts > 0 &&
							 SourceList.IndexOf(o) == Math.Floor(Rotation.NumInstruments / 2.0) - 1)
					{
						DoPrint("[Rotation] Reached Halfway Point, Accepting Fewer Instruments | Instruments = " + NewList.Count + " / " + Rotation.NumLongs);
						break;
					}
				}
			}

			if (NewList.Count < Rotation.NumLongs)
				DoPrint("[Rotation] Smaller Long List Finalized | Instruments = " + NewList.Count + " / " + Rotation.NumLongs);
			#endregion
		}
		#endregion
		// Creates a new list of desired longs.

		#region GenerateShortList
		private void GenerateShortList(List<InstrumentClass> SourceList, ref List<InstrumentClass> NewList)
		{
			#region Reporting/Housekeeping
			if (!Rotation.RotationShortFilter)
				DoPrint("[Rotation] Generating New Short List (Unfiltered)");
			else
				DoPrint("[Rotation] Generating New Short List (Filtered)");

			if (Rotation.RotationInverseMode)
				DoPrint("[Rotation] Inverse Mode Activated, Shorting Highest Scores");
			if (Rotation.SkipTopShorts > 0)
				DoPrint("[Rotation] Skipping Top Shorts | Skipped = " + Rotation.SkipTopShorts);

			// Clear the previous list.
			NewList.Clear();
			#endregion

			// Sort the source list.
			#region SourceList Sorting
			// If inverse mode is set to 1, we sort from lowest to highest and buy those with low scores.
			if (!Rotation.RotationInverseMode)
				SortListByScore(ref SourceList, true);
			else
				SortListByScore(ref SourceList, false);
			#endregion

			// Form the new list.
			#region NewList Creation
			foreach (InstrumentClass o in SourceList)
			{
				if (SourceList.IndexOf(o) <= Rotation.SkipTopShorts - 1)
					DoPrint ("Skipping Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
				else if (!ShortFilter(o))
				{
					NewList.Add(o);
					DoPrint ("Adding Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
				}

				// Insert break conditions here.
				// Stop when we have gotten the number of items we wanted.
				if (NewList.Count >= Rotation.NumShorts)
				{
					DoPrint("[Rotation] Full Short List Created Successfully | Instruments = " + NewList.Count + " / " + Rotation.NumShorts);
					break;
				}
				// If we have longs, we don't progress further than halfway down the list.
				else if (Rotation.RotationLongFilter &&
						 Rotation.NumLongs > 0 &&
					 	 SourceList.IndexOf(o) == Math.Floor(Rotation.NumInstruments / 2.0) - 1)
				{
					DoPrint("[Rotation] Reached Halfway Point | Instruments = " + NewList.Count + " / " + Rotation.NumShorts);
					break;
				}
			}
			#endregion

			// Check FilterMode and act, if insufficient instruments are added to the list.
			#region FilterMode Pass
			// If set to 2, bypass the filter and accept highest/lowest scorers, regardless of whether or not they pass the filter to maintain size.
			if (Rotation.FilterMode == 2 &&
				NewList.Count < Rotation.NumShorts)
			{
				DoPrint("[Rotation] Maintaining Desired Size w/ Bypasses");

				foreach (InstrumentClass o in SourceList)
				{
					if (NewList.Any(p => p.Symbol == o.Symbol))
						DoPrint("Existing Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					else
					{
						NewList.Add(o);
						DoPrint("Adding Bypassed Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					}

					// Insert break conditions here.
					// If we have gotten the number of items we wanted.
					if (NewList.Count >= Rotation.NumShorts)
					{
						DoPrint("[Rotation] Full Short List Created Successfully w/ Bypasses | Instruments = " + NewList.Count + " / " + Rotation.NumShorts);
						break;
					}
					// If we have longs, we don't progress further than halfway down the list.
					else if (Rotation.RotationLongFilter &&
							 Rotation.NumLongs > 0 &&
							 SourceList.IndexOf(o) == Math.Floor(Rotation.NumInstruments / 2.0) - 1)
					{
						DoPrint("[Rotation] Reached Halfway Point, Accepting Fewer Instruments | Instruments = " + NewList.Count + " / " + Rotation.NumShorts);
						break;
					}
				}
			}
			// If set to 1, do nothing unless we have insufficient instruments in the list, in which case bypass the filter till we have FilterMinSize instruments.
			else if (Rotation.FilterMode == 1 &&
					 NewList.Count < Rotation.FilterMinSize)
			{
				DoPrint("[Rotation] Reaching Minimum Size w/ Bypasses | Minimum Size = " + Rotation.FilterMinSize);

				foreach (InstrumentClass o in SourceList)
				{
					if (NewList.Any(p => p.Symbol == o.Symbol))
						DoPrint("Existing Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					else
					{
						NewList.Add(o);
						DoPrint("Adding Bypassed Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					}

					// Insert break conditions here.
					// Stop when we have gotten the number of items we wanted.
					if (NewList.Count >= Rotation.FilterMinSize)
					{
						DoPrint("[Rotation] Minimum Size Short List Created | Instruments = " + NewList.Count + " / " + Rotation.FilterMinSize);
						break;
					}
					// If we have longs, we don't progress further than halfway down the list.
					else if (Rotation.RotationLongFilter &&
							 Rotation.NumLongs > 0 &&
							 SourceList.IndexOf(o) == Math.Floor(Rotation.NumInstruments / 2.0) - 1)
					{
						DoPrint("[Rotation] Reached Halfway Point, Accepting Fewer Instruments | Instruments = " + NewList.Count + " / " + Rotation.NumShorts);
						break;
					}
				}
			}

			if (NewList.Count < Rotation.NumShorts)
				DoPrint("[Rotation] Smaller Short List Finalized | Instruments = " + NewList.Count + " / " + Rotation.NumShorts);
			#endregion
		}
		#endregion
		// Creates a new list of desired shorts.

		#region GenerateCutoffLongList
		private void GenerateCutoffLongList(List<InstrumentClass> SourceList, ref List<InstrumentClass> NewList)
		{
			#region Reporting/Housekeeping
			if (!Rotation.RotationLongFilter)
				DoPrint("[Rotation] Generating New Cutoff Long List (Unfiltered) | Threshold = " + Rotation.CutoffLongThreshold + " | Maximum Size = " + Rotation.CutoffMaxSize);
			else
				DoPrint("[Rotation] Generating New Cutoff Long List (Filtered) | Threshold = " + Rotation.CutoffLongThreshold + " | Maximum Size = " + Rotation.CutoffMaxSize);

			if (Rotation.RotationInverseMode)
				DoPrint("[Rotation] Inverse Mode Activated, Buying Lowest Scores");
			if (Rotation.SkipTopLongs > 0)
				DoPrint("[Rotation] Skipping Top Longs | Skipped = " + Rotation.SkipTopLongs);

			// Clear the previous list.
			NewList.Clear();
			Rotation.LongCutoffHit	= false;
			#endregion

			// Sort the source list.
			#region SourceList Sorting
			// If inverse mode is set to 1, we sort from lowest to highest and buy those with low scores.
			if (!Rotation.RotationInverseMode)
				SortListByScore(ref SourceList, false);
			else
				SortListByScore(ref SourceList, true);
			#endregion

			// Form the new cutoff list.
			#region NewList Creation
			foreach (InstrumentClass o in SourceList)
			{
				if (SourceList.IndexOf(o) <= Rotation.SkipTopLongs - 1)
					DoPrint ("Skipping Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
				else if (!LongFilter(o))
				{
					NewList.Add(o);
					DoPrint ("Adding Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
				}

				// Insert break conditions here.
				// Stop when the threshold has been hit (detected in LongFilter method).
				if (Rotation.LongCutoffHit)
				{
					DoPrint("[Rotation] Cutoff Long List Created Successfully, Threshold Hit | Instruments = " + NewList.Count);
					break;
				}
				// Stop when we reach the maximum defined size, if there is one.
				else if (Rotation.CutoffMaxSize != 0 &&
						 NewList.Count == Rotation.CutoffMaxSize)
				{
					DoPrint("[Rotation] Cutoff Long List Maximum Size Hit | Instruments = " + NewList.Count + " / " + Rotation.CutoffMaxSize);
					break;
				}
			}
			#endregion

			// Check FilterMode and act, if insufficient instruments are added to the list.
			#region FilterMode Pass
			// If set to 1, do nothing unless we have insufficient instruments in the list, in which case bypass the filter until we have FilterMinSize instruments.
			if (Rotation.FilterMode == 1 &&
				NewList.Count < Rotation.FilterMinSize)
			{
				DoPrint("[Rotation] Reaching Minimum Size w/ Bypasses | Minimum Size = " + Rotation.FilterMinSize);

				foreach (InstrumentClass o in SourceList)
				{
					if (NewList.Any(p => p.Symbol == o.Symbol))
						DoPrint("Existing Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					else
					{
						NewList.Add(o);
						DoPrint("Adding Bypassed Long > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					}

					// Insert break conditions here.
					// Stop when we have gotten the number of items we wanted.
					if (NewList.Count >= Rotation.FilterMinSize)
					{
						DoPrint("[Rotation] Minimum Size Cutoff Long List Created | Instruments = " + NewList.Count + " / " + Rotation.FilterMinSize);
						break;
					}
				}
			}

			if (NewList.Count < Rotation.FilterMinSize)
				DoPrint("[Rotation] Smaller Cutoff Long List Finalized | Instruments = " + NewList.Count + " / " + Rotation.FilterMinSize);
			#endregion
		}
		#endregion
		// Creates a new cutoff list of desired longs.

		#region GenerateCutoffShortList
		private void GenerateCutoffShortList(List<InstrumentClass> SourceList, ref List<InstrumentClass> NewList)
		{
			#region Reporting/Housekeeping
			if (!Rotation.RotationShortFilter)
				DoPrint("[Rotation] Generating New Cutoff Short List (Unfiltered) | Threshold = " + Rotation.CutoffShortThreshold + " | Maximum Size = " + Rotation.CutoffMaxSize);
			else
				DoPrint("[Rotation] Generating New Cutoff Short List (Filtered) | Threshold = " + Rotation.CutoffShortThreshold + " | Maximum Size = " + Rotation.CutoffMaxSize);

			if (Rotation.RotationInverseMode)
				DoPrint("[Rotation] Inverse Mode Activated, Shorting Highest Scores");
			if (Rotation.SkipTopShorts > 0)
				DoPrint("[Rotation] Skipping Top Short Values | Skipped = " + Rotation.SkipTopShorts);

			// Clear the previous list.
			NewList.Clear();
			Rotation.ShortCutoffHit	= false;
			#endregion

			// Sort the source list.
			#region SourceList Sorting
			// If inverse mode is set to 1, we sort from lowest to highest and buy those with low scores.
			if (!Rotation.RotationInverseMode)
				SortListByScore(ref SourceList, true);
			else
				SortListByScore(ref SourceList, false);
			#endregion

			// Form the new cutoff list.
			#region NewList Creation
			foreach (InstrumentClass o in SourceList)
			{
				if (SourceList.IndexOf(o) <= Rotation.SkipTopShorts - 1)
					DoPrint ("Skipping Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
				else if (!ShortFilter(o))
				{
					NewList.Add(o);
					DoPrint ("Adding Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
				}

				// Insert break conditions here.
				// Stop when the threshold has been hit (detected in ShortFilter method).
				if (Rotation.ShortCutoffHit)
				{
					DoPrint("[Rotation] Cutoff Short List Created Successfully, Threshold Hit | Instruments = " + NewList.Count);
					break;
				}
				// Stop when we reach the maximum defined size, if there is one.
				else if (Rotation.CutoffMaxSize != 0 &&
						 NewList.Count == Rotation.CutoffMaxSize)
				{
					DoPrint("[Rotation] Cutoff Short List Maximum Size Hit | Instruments = " + NewList.Count + " / " + Rotation.CutoffMaxSize);
					break;
				}
			}
			#endregion

			// Check FilterMode and act, if insufficient instruments are added to the list.
			#region FilterMode Pass
			// If set to 1, do nothing unless we have insufficient instruments in the list, in which case bypass the filter until we have FilterMinSize instruments.
			if (Rotation.FilterMode == 1 &&
				NewList.Count < Rotation.FilterMinSize)
			{
				DoPrint("[Rotation] Reaching Minimum Size w/ Bypasses | Minimum Size = " + Rotation.FilterMinSize);

				foreach (InstrumentClass o in SourceList)
				{
					if (NewList.Any(p => p.Symbol == o.Symbol))
						DoPrint("Existing Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					else
					{
						NewList.Add(o);
						DoPrint("Adding Bypassed Short > " + o.Symbol + "[" + o.Index + "] = " + Math.Round(o.Score, 2));
					}

					// Insert break conditions here.
					// Stop when we have gotten the number of items we wanted.
					if (NewList.Count >= Rotation.FilterMinSize)
					{
						DoPrint("[Rotation] Minimum Size Cutoff Short List Created | Instruments = " + NewList.Count + " / " + Rotation.FilterMinSize);
						break;
					}
				}
			}

			if (NewList.Count < Rotation.FilterMinSize)
				DoPrint("[Rotation] Smaller Cutoff Short List Finalized | Instruments = " + NewList.Count + " / " + Rotation.FilterMinSize);
			#endregion
		}
		#endregion
		// Creates a new cutoff list of desired shorts.

		#region ReportCurrentExposure
		private void ReportCurrentExposure()
		{
			DoPrint("# List: CurrentLongList (" + CurrentLongList.Count + ")");
			PrintList(CurrentLongList, 2);
			//PrintList(CurrentLongList, 4);
			DoPrint("# List: CurrentShortList (" + CurrentShortList.Count + ")");
			PrintList(CurrentShortList, 2);
			//PrintList(CurrentShortList, 4);
		}
		#endregion


	//------	Trade Halts / Entry Filters		------

		#region CheckTradeHalts
		private bool CheckTradeHalts()
		{
			if (States.BypassTradeHalts)
				return false;

			if (TradeHaltPresets(States.NowTradeHalted, Metrics, TradedList))
				return true;

			// Strategy specific checks.
			//
			//
			//-----------

			// Returns false if trading is allowed.
			return false;
		}
		#endregion
		// Checks trade halts - maximum daily loss limit and strategy specific conditions. Can also be bypassed.
		// Returns true if trade is to be halted, otherwise returns false.
		// Edit:				Strategy specific trade halt conditions.
		// Related Methods:		TradeHaltPresets(NowTradeHalted, Metrics)

		#region CheckEntryFilters
		private bool CheckEntryFilters()
		{
			if (States.BypassEntryFilters)
				return false;

			if (EntryFilterPresets(States.NowFiltered, Metrics, TradedList))
				return true;

			if (IsFirstTickOfBar &&
				MinReentryBars > 0 &&
				TimeEntryFilter(false, States.NowFiltered, MinReentryBars, TradedList, 0))
				return true;

			// Strategy specific checks.
			//
			//
			//-----------

			// Returns false if trading is allowed.
			return false;
		}
		#endregion
		// Checks entry filters - time filter and strategy specific conditions. Can also be bypassed.
		// Returns true if entry is to be blocked, otherwise returns false.
		// Edit:				Strategy specific entry filters.
		//						Time filter logic for additional instruments (default is the main instrument only).
		// Related Methods:		EntryFilterPresets(NowFiltered, Metrics, TradedList)
		//						TimeEntryFilter(ShowOutput, NowFiltered, MinReentryBars, TradedList, BarsArrayRef)


	//------	Other Methods		------

		#region DoFlatten
		private void DoFlatten(string ReasonString)
		{
			foreach (InstrumentClass o in TradedList)
			{
				if (o.HasPosition)
				{
					ExitLong(o.Index, 0, "ExitFlatten", "");
					ExitShort(o.Index, 0, "ExitFlatten", "");

					DecisionInfo	= "# Signal: [Flattenning] " + ReasonString + " " + o.Symbol + " | Exposure = " + (GetExposure(o.Index)).ToString("C");
					GenerateDecisionString(Reports.MailNotifications, ref DecisionInfo, ref o.DecisionString, ref o.DecisionPrice, o.Index);

					// Enforces a cooldown period after a flatten event.
					Rotation.NextDecisionTime = Rotation.CurrentTimeSeries + Rotation.DecisionFrequency;
				}
			}
		}
		// Overloads.
		private void DoFlatten()
		{
			DoFlatten(null);
		}

//		private static T _download_serialized_json_data<T>(string url) where T : new() {
//		   using (var w = new WebClient()) {
//		    var json_data = string.Empty;
//		    // attempt to download JSON data as a string
//		    try {
//		      json_data = w.DownloadString(url);
//		    }
//		    catch (Exception) {}
//		    // if string with JSON data is not empty, deserialize it to class and return its instance
//		    return !string.IsNullOrEmpty(json_data) ? JsonConvert.DeserializeObject<T>(json_data) : new T();
//		  }
//		}


		#endregion
		// Flattens positions for all instruments. Used at end of sessions if ControlFlatten is selected, or if a trade halt is flagged.


	//------	Variables	------

		#region Properties

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "RefInstrument", GroupName = "1. Strategy Specific", Order = 0)]
		public string RefInstrument
		{ get; set; }

		[Display(ResourceType = typeof(Custom.Resource), Name = "dbTableLong", GroupName = "1. Strategy Specific", Order = 1)]
		public string dbTableLong
		{ get; set; }

		[Display(ResourceType = typeof(Custom.Resource), Name = "dbTableShort", GroupName = "1. Strategy Specific", Order = 2)]
		public string dbTableShort
		{ get; set; }

		[Range(0, 1.1), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "BuySignalThreshold", GroupName = "1. Strategy Specific", Order = 3)]
		public double BuySignalThreshold
		{ get; set; }

		[Range(0, 1.1), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "SellSignalThreshold", GroupName = "1. Strategy Specific", Order = 4)]
		public double SellSignalThreshold
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "ConsecutiveSignalBars", GroupName = "1. Strategy Specific", Order = 5)]
		public int ConsecutiveSignalBars
		{ get; set; }

		[Range(0, 2), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "OrderType", GroupName = "1. Strategy Specific", Order = 8)]
		public int OrderType
		{ get; set; }


	// --------------------

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "SignalLag", GroupName = "2. SQL Related", Order = 0)]
		public int SignalLag
		{ get; set; }


	// --------------------


	// --------------------

		[Range(0, 3), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "AllocationMethod", GroupName = "3. Capital Allocation", Order = 0)]
		public int AllocationMethod
		{ get; set; }

		[Range(0, double.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "InitialCapital", GroupName = "3. Capital Allocation", Order = 1)]
		public double InitialCapital
		{ get; set; }

		[Range(0, 100), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "ReinvestmentPct", GroupName = "3. Capital Allocation", Order = 2)]
		public double ReinvestmentPct
		{ get; set; }

		[Range(0, 5), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "LeverageFactor", GroupName = "3. Capital Allocation", Order = 3)]
		public double LeverageFactor
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "FixedSize", GroupName = "3. Capital Allocation", Order = 4)]
		public bool FixedSize
		{ get; set; }

	// --------------------

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "MaxDailyTrades", GroupName = "4. Other Presets", Order = 0)]
		public int MaxDailyTrades
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "MaxDailyLosses", GroupName = "4. Other Presets", Order = 1)]
		public int MaxDailyLosses
		{ get; set; }

		[Range(0, 100), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "MaxDailyLossPct", GroupName = "4. Other Presets", Order = 2)]
		public double MaxDailyLossPct
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "TimeStopBars", GroupName = "4. Other Presets", Order = 3)]
		public int TimeStopBars
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "MinReentryBars", GroupName = "4. Other Presets", Order = 4)]
		public int MinReentryBars
		{ get; set; }

		[Range(0, 100), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "StopLossPct", GroupName = "4. Other Presets", Order = 5)]
		public double StopLossPct
		{ get; set; }

		[Range(0, 100), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "TargetProfitPct", GroupName = "4. Other Presets", Order = 6)]
		public double TargetProfitPct
		{ get; set; }

		[Range(0, 100), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "TrailStopPct", GroupName = "4. Other Presets", Order = 7)]
		public double TrailStopPct
		{ get; set; }

	// --------------------

		[Range(0, 3), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "Sessions", GroupName = "5. Sessions", Order = 0)]
		public int Sessions
		{ get; set; }

		[Range(0, 2400), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "S1Begin", GroupName = "5. Sessions", Order = 1)]
		public int S1Begin
		{ get; set; }

		[Range(0, 2400), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "S1End", GroupName = "5. Sessions", Order = 2)]
		public int S1End
		{ get; set; }

		[Range(0, 2400), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "S2Begin", GroupName = "5. Sessions", Order = 3)]
		public int S2Begin
		{ get; set; }

		[Range(0, 2400), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "S2End", GroupName = "5. Sessions", Order = 4)]
		public int S2End
		{ get; set; }

		[Range(0, 2400), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "S3Begin", GroupName = "5. Sessions", Order = 5)]
		public int S3Begin
		{ get; set; }

		[Range(0, 2400), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "S3End", GroupName = "5. Sessions", Order = 6)]
		public int S3End
		{ get; set; }

		[Range(0, 2400), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "BlockEntryTime", GroupName = "5. Sessions", Order = 7)]
		public int BlockEntryTime
		{ get; set; }

		[Range(0, 2400), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "FlattenTime", GroupName = "5. Sessions", Order = 8)]
		public int FlattenTime
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "ControlFlatten", GroupName = "5. Sessions", Order = 9)]
		public bool ControlFlatten
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "OutOfSessionExit", GroupName = "5. Sessions", Order = 10)]
		public bool OutOfSessionExit
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "BypassEntryFilters", GroupName = "5. Sessions", Order = 11)]
		public bool BypassEntryFilters
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "BypassTradeHalts", GroupName = "5. Sessions", Order = 12)]
		public bool BypassTradeHalts
		{ get; set; }

	// --------------------

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "LogDirectoryPath", GroupName = "6. Reporting", Order = 0)]
		public string LogDirectoryPath
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "BacktestSummary", GroupName = "6. Reporting", Order = 1)]
		public bool BacktestSummary
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "EvolutionSummary", GroupName = "6. Reporting", Order = 2)]
		public bool EvolutionSummary
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "WriteOutput", GroupName = "6. Reporting", Order = 3)]
		public bool WriteOutput
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "MailNotifications", GroupName = "6. Reporting", Order = 4)]
		public bool MailNotifications
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "DisplayStatusBox", GroupName = "6. Reporting", Order = 5)]
		public bool DisplayStatusBox
		{ get; set; }

	// --------------------

		[Range(1, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "NumInstruments", GroupName = "7.1. Rotation / Basic", Order = 0)]
		public int NumInstruments
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "NumLongs", GroupName = "7.1. Rotation / Basic", Order = 1)]
		public int NumLongs
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "NumShorts", GroupName = "7.1. Rotation / Basic", Order = 2)]
		public int NumShorts
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "TradableStartIndex", GroupName = "7.1. Rotation / Basic", Order = 3)]
		public int TradableStartIndex
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "DecisionFrequency", GroupName = "7.1. Rotation / Basic", Order = 4)]
		public int DecisionFrequency
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "OrderDelayBars", GroupName = "7.1. Rotation / Basic", Order = 5)]
		public int OrderDelayBars
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "RebalanceFrequency", GroupName = "7.1. Rotation / Basic", Order = 6)]
		public int RebalanceFrequency
		{ get; set; }

		[Range(0, double.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "RebalanceThreshold", GroupName = "7.1. Rotation / Basic", Order = 7)]
		public double RebalanceThreshold
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "RotationInverseMode", GroupName = "7.1. Rotation / Basic", Order = 8)]
		public bool RotationInverseMode
		{ get; set; }

	// --------------------

		[Range(0, 2), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "FilterMode", GroupName = "7.2. Rotation / Filter", Order = 0)]
		public int FilterMode
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "FilterMinSize", GroupName = "7.2. Rotation / Filter", Order = 1)]
		public int FilterMinSize
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "SkipTopLongs", GroupName = "7.2. Rotation / Filter", Order = 2)]
		public int SkipTopLongs
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "SkipTopShorts", GroupName = "7.2. Rotation / Filter", Order = 3)]
		public int SkipTopShorts
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "RotationLongFilter", GroupName = "7.2. Rotation / Filter", Order = 4)]
		public bool RotationLongFilter
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "RotationShortFilter", GroupName = "7.2. Rotation / Filter", Order = 5)]
		public bool RotationShortFilter
		{ get; set; }

	// --------------------

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "RotationCutoffMode", GroupName = "7.3. Rotation / Cutoff", Order = 0)]
		public bool RotationCutoffMode
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "CutoffLongThreshold", GroupName = "7.3. Rotation / Cutoff", Order = 1)]
		public double CutoffLongThreshold
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "CutoffShortThreshold", GroupName = "7.3. Rotation / Cutoff", Order = 2)]
		public double CutoffShortThreshold
		{ get; set; }

		[Range(0, int.MaxValue), NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "CutoffMaxSize", GroupName = "7.3. Rotation / Cutoff", Order = 3)]
		public int CutoffMaxSize
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "RotationCutoffLongs", GroupName = "7.3. Rotation / Cutoff", Order = 4)]
		public bool RotationCutoffLongs
		{ get; set; }

		[NinjaScriptProperty]
		[Display(ResourceType = typeof(Custom.Resource), Name = "RotationCutoffShorts", GroupName = "7.3. Rotation / Cutoff", Order = 5)]
		public bool RotationCutoffShorts
		{ get; set; }
		#endregion
	}
}
